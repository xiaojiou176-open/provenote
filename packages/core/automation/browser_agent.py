"""Browser agent loop skeleton: observe -> decide -> act -> observe."""

from __future__ import annotations

import asyncio
import inspect
import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol, cast

from packages.core.ai.model_strategy import GEMINI_LANGUAGE_MODEL_PRIORITY
from packages.core.automation.browser_actions import (
    DEFAULT_BROWSER_AGENT_MODEL,
    BrowserAction,
    BrowserActionPlan,
    ensure_actions_safe,
    parse_action_plan,
)
from packages.core.automation.policy_engine import (
    BrowserPolicyEngine,
    PolicyDecision,
    build_policy_context,
    has_confirmation_semantics,
    is_high_risk_action,
)

DEFAULT_MODEL_PRIORITY: tuple[str, ...] = (
    DEFAULT_BROWSER_AGENT_MODEL,
    *GEMINI_LANGUAGE_MODEL_PRIORITY,
)


class BrowserObserver(Protocol):
    def observe(self) -> dict[str, Any] | Awaitable[dict[str, Any]]: ...


class BrowserDecider(Protocol):
    def decide(
        self,
        objective: str,
        observation: dict[str, Any],
        model_id: str,
        model_priority: tuple[str, ...],
    ) -> (
        str
        | dict[str, Any]
        | list[dict[str, Any]]
        | Awaitable[str | dict[str, Any] | list[dict[str, Any]]]
    ): ...


class BrowserExecutor(Protocol):
    def execute(
        self, action: BrowserAction
    ) -> dict[str, Any] | Awaitable[dict[str, Any]]: ...


ActionConfirmer = Callable[[BrowserAction, str, str], bool | Awaitable[bool]]
GoalChecker = Callable[[str, dict[str, Any], int, str], bool | Awaitable[bool]]
AuditLogger = Callable[[dict[str, Any]], None]
PolicyContextResolver = Callable[
    [BrowserAction, str, dict[str, Any]], dict[str, Any] | Awaitable[dict[str, Any]]
]


class ConfirmationRequiredError(RuntimeError):
    """Raised when a high-risk action requires explicit confirmation."""


class PolicyDeniedError(RuntimeError):
    """Raised when policy decision explicitly denies an action."""


_REDACTED_VALUE = "[REDACTED]"
_SENSITIVE_AUDIT_KEYS = frozenset(
    {
        "text",
        "value",
        "content",
        "payload",
        "input",
        "prompt",
        "upload_text",
        "file_name",
        "file_path",
        "path",
        "data",
        "body",
    }
)
_SIDE_EFFECT_TOKENS = (
    "delete",
    "remove",
    "submit",
    "send",
    "transfer",
    "wire",
    "pay",
    "purchase",
    "checkout",
    "confirm",
    "upload",
    "paste",
    "type",
)


@dataclass(slots=True)
class BrowserStepResult:
    run_id: str
    step_id: str
    step_index: int
    observation_before: dict[str, Any]
    action_plan: BrowserActionPlan
    action_results: list[dict[str, Any]]
    observation_after: dict[str, Any]
    goal_reached: bool = False


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await cast(Awaitable[Any], value)
    return value


class BrowserAgent:
    """Testable browser automation agent core without hard dependency on browser runtime."""

    def __init__(
        self,
        observer: BrowserObserver,
        decider: BrowserDecider,
        executor: BrowserExecutor,
        *,
        model_id: str = DEFAULT_BROWSER_AGENT_MODEL,
        max_steps: int = 5,
        max_retries: int = 0,
        action_timeout_seconds: float | None = 10.0,
        confirm_action: ActionConfirmer | None = None,
        goal_checker: GoalChecker | None = None,
        audit_logger: AuditLogger | None = None,
        policy_engine: BrowserPolicyEngine | None = None,
        policy_context_resolver: PolicyContextResolver | None = None,
    ) -> None:
        self.observer = observer
        self.decider = decider
        self.executor = executor
        self.model_id = model_id
        self.max_steps = max_steps
        self.max_retries = max_retries
        self.action_timeout_seconds = action_timeout_seconds
        self.confirm_action = confirm_action
        self.goal_checker = goal_checker
        self.audit_logger = audit_logger
        self.policy_engine = policy_engine or BrowserPolicyEngine()
        self.policy_context_resolver = policy_context_resolver

        ordered = [model_id, *DEFAULT_MODEL_PRIORITY]
        seen: set[str] = set()
        deduplicated: list[str] = []
        for model_name in ordered:
            if model_name in seen:
                continue
            seen.add(model_name)
            deduplicated.append(model_name)
        self.model_priority = tuple(deduplicated)

    def _emit_audit_event(self, event: dict[str, Any]) -> None:
        if self.audit_logger is not None:
            self.audit_logger(event)

    def _sanitize_action_for_audit(self, action: BrowserAction) -> dict[str, Any]:
        payload = action.model_dump(mode="json")
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            lowered = key.lower()
            if lowered in _SENSITIVE_AUDIT_KEYS or lowered.endswith("_text"):
                redacted[key] = _REDACTED_VALUE
                continue
            if (
                isinstance(value, str)
                and lowered == "action"
                and value.lower() in {"type", "paste", "upload"}
            ):
                redacted["input_redacted"] = True
            redacted[key] = value
        return redacted

    def _is_non_idempotent_side_effect(self, action: BrowserAction) -> bool:
        if action.action == "type":
            return True
        if action.action != "click":
            return False
        selector = getattr(action, "selector", "").lower()
        return any(token in selector for token in _SIDE_EFFECT_TOKENS)

    async def _resolve_policy_context(
        self,
        action: BrowserAction,
        objective: str,
        observation_before: dict[str, Any],
    ) -> dict[str, Any]:
        context = build_policy_context(
            observation=observation_before, operation_intent=objective
        )
        if self.policy_context_resolver is None:
            return context
        resolved = await _maybe_await(
            self.policy_context_resolver(action, objective, observation_before)
        )
        return build_policy_context(
            observation=observation_before, operation_intent=objective, extra=resolved
        )

    async def run_step(
        self, objective: str, step_index: int = 0, *, run_id: str | None = None
    ) -> BrowserStepResult:
        resolved_run_id = run_id or uuid.uuid4().hex
        step_id = f"{resolved_run_id}:{step_index}"
        observation_before = await _maybe_await(self.observer.observe())
        raw_plan = await _maybe_await(
            self.decider.decide(
                objective=objective,
                observation=observation_before,
                model_id=self.model_id,
                model_priority=self.model_priority,
            )
        )

        action_plan = parse_action_plan(raw_plan)
        ensure_actions_safe(action_plan)

        action_results: list[dict[str, Any]] = []
        for action in action_plan.actions:
            policy_context = await self._resolve_policy_context(
                action, objective, observation_before
            )
            policy_result = self.policy_engine.evaluate(action, context=policy_context)

            if policy_result.decision is PolicyDecision.DENY:
                deny_error = PolicyDeniedError(
                    f"Policy denied action '{action.action}' via rule '{policy_result.rule_name}'"
                )
                self._emit_audit_event(
                    {
                        "run_id": resolved_run_id,
                        "step_id": step_id,
                        "action": self._sanitize_action_for_audit(action),
                        "result": "blocked",
                        "error": str(deny_error),
                        "retry_count": 0,
                        "policy_decision": policy_result.decision.value,
                        "policy_rule": policy_result.rule_name,
                    }
                )
                raise deny_error

            if policy_result.decision is PolicyDecision.CONFIRM:
                if is_high_risk_action(
                    action, policy_context
                ) and not has_confirmation_semantics(policy_context):
                    confirmation_error = ConfirmationRequiredError(
                        f"Confirmation semantics required for high-risk action: {action.action}"
                    )
                    self._emit_audit_event(
                        {
                            "run_id": resolved_run_id,
                            "step_id": step_id,
                            "action": self._sanitize_action_for_audit(action),
                            "result": "blocked",
                            "error": str(confirmation_error),
                            "retry_count": 0,
                            "policy_decision": policy_result.decision.value,
                            "policy_rule": policy_result.rule_name,
                        }
                    )
                    raise confirmation_error
                confirmed = False
                if self.confirm_action is not None:
                    confirmed = bool(
                        await _maybe_await(
                            self.confirm_action(action, step_id, resolved_run_id)
                        )
                    )
                if not confirmed:
                    confirmation_error = ConfirmationRequiredError(
                        f"Confirmation required for high-risk action: {action.action}"
                    )
                    self._emit_audit_event(
                        {
                            "run_id": resolved_run_id,
                            "step_id": step_id,
                            "action": self._sanitize_action_for_audit(action),
                            "result": "blocked",
                            "error": str(confirmation_error),
                            "retry_count": 0,
                            "policy_decision": policy_result.decision.value,
                            "policy_rule": policy_result.rule_name,
                        }
                    )
                    raise confirmation_error

            retry_count = 0
            retry_allowed = not self._is_non_idempotent_side_effect(action)
            if is_high_risk_action(action, policy_context):
                retry_allowed = False
            while True:
                try:
                    execution = _maybe_await(self.executor.execute(action))
                    if self.action_timeout_seconds is None:
                        result = await execution
                    else:
                        result = await asyncio.wait_for(
                            execution, timeout=self.action_timeout_seconds
                        )
                    action_results.append(result)
                    self._emit_audit_event(
                        {
                            "run_id": resolved_run_id,
                            "step_id": step_id,
                            "action": self._sanitize_action_for_audit(action),
                            "result": "success",
                            "error": None,
                            "retry_count": retry_count,
                            "policy_decision": policy_result.decision.value,
                            "policy_rule": policy_result.rule_name,
                        }
                    )
                    break
                except Exception as exc:
                    self._emit_audit_event(
                        {
                            "run_id": resolved_run_id,
                            "step_id": step_id,
                            "action": self._sanitize_action_for_audit(action),
                            "result": "error",
                            "error": str(exc),
                            "retry_count": retry_count,
                            "policy_decision": policy_result.decision.value,
                            "policy_rule": policy_result.rule_name,
                        }
                    )
                    if retry_count >= self.max_retries or not retry_allowed:
                        raise
                    retry_count += 1

        observation_after = await _maybe_await(self.observer.observe())
        goal_reached = False
        if self.goal_checker is not None:
            goal_reached = bool(
                await _maybe_await(
                    self.goal_checker(
                        objective, observation_after, step_index, resolved_run_id
                    )
                )
            )
        return BrowserStepResult(
            run_id=resolved_run_id,
            step_id=step_id,
            step_index=step_index,
            observation_before=observation_before,
            action_plan=action_plan,
            action_results=action_results,
            observation_after=observation_after,
            goal_reached=goal_reached,
        )

    async def run(
        self, objective: str, *, steps: int | None = None
    ) -> list[BrowserStepResult]:
        total_steps = steps if steps is not None else self.max_steps
        if total_steps < 1:
            raise ValueError("steps must be >= 1")

        results: list[BrowserStepResult] = []
        run_id = uuid.uuid4().hex
        for step in range(total_steps):
            step_result = await self.run_step(
                objective=objective, step_index=step, run_id=run_id
            )
            results.append(step_result)
            if step_result.goal_reached:
                break
        return results

    def run_sync(
        self, objective: str, *, steps: int | None = None
    ) -> list[BrowserStepResult]:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run(objective=objective, steps=steps))
        raise RuntimeError("run_sync cannot be used from inside an active event loop")


__all__ = [
    "BrowserAgent",
    "BrowserDecider",
    "BrowserExecutor",
    "BrowserObserver",
    "BrowserStepResult",
    "ConfirmationRequiredError",
    "DEFAULT_MODEL_PRIORITY",
    "PolicyDeniedError",
]

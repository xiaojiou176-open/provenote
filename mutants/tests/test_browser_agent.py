from __future__ import annotations

import asyncio

import pytest

from packages.core.automation.browser_actions import (
    ActionParseError,
    ClickAction,
    DangerousActionError,
    TypeAction,
    WaitAction,
    action_requires_confirmation,
    parse_action_plan,
)
from packages.core.automation.browser_agent import (
    BrowserAgent,
    ConfirmationRequiredError,
    PolicyDeniedError,
)
from packages.core.automation.policy_engine import (
    BrowserPolicyEngine,
    PolicyDecision,
    PolicyRule,
)


class FakeObserver:
    def __init__(self) -> None:
        self.calls = 0

    def observe(self) -> dict[str, object]:
        self.calls += 1
        return {"url": "https://example.com", "tick": self.calls}


class FakeExecutor:
    def __init__(self) -> None:
        self.actions: list[str] = []

    def execute(self, action) -> dict[str, object]:
        self.actions.append(action.action)
        return {"ok": True, "action": action.action}


class FakeDecider:
    def __init__(self, raw_plan):
        self.raw_plan = raw_plan
        self.calls = 0
        self.last_model_id: str | None = None
        self.last_model_priority: tuple[str, ...] | None = None

    def decide(self, objective, observation, model_id, model_priority):
        self.calls += 1
        self.last_model_id = model_id
        self.last_model_priority = model_priority
        return self.raw_plan


def test_parse_action_plan_accepts_whitelisted_actions() -> None:
    plan = parse_action_plan(
        {
            "actions": [
                {"action": "click", "selector": "button[type='submit']"},
                {"action": "type", "selector": "#q", "text": "hello"},
                {"action": "scroll", "direction": "down", "amount": 500},
                {"action": "wait", "duration_ms": 800},
            ]
        }
    )

    assert len(plan.actions) == 4
    assert isinstance(plan.actions[1], TypeAction)


def test_parse_action_plan_rejects_non_whitelisted_action() -> None:
    with pytest.raises(ActionParseError):
        parse_action_plan({"actions": [{"action": "navigate", "url": "https://x.com"}]})


def test_parse_action_plan_blocks_dangerous_selector() -> None:
    plan = parse_action_plan(
        {"actions": [{"action": "click", "selector": "a[href='javascript:alert(1)']"}]}
    )

    from packages.core.automation.browser_actions import ensure_actions_safe

    with pytest.raises(DangerousActionError):
        ensure_actions_safe(plan)


def test_browser_agent_run_sync_executes_observe_decide_act_cycle() -> None:
    observer = FakeObserver()
    executor = FakeExecutor()
    decider = FakeDecider({"actions": [{"action": "wait", "duration_ms": 100}]})

    agent = BrowserAgent(observer=observer, decider=decider, executor=executor)
    results = agent.run_sync("load page", steps=1)

    assert len(results) == 1
    assert observer.calls == 2
    assert decider.calls == 1
    assert executor.actions == ["wait"]
    assert decider.last_model_id == "gemini-3.1-pro"
    assert decider.last_model_priority == (
        "gemini-3.1-pro",
        "gemini-3.0-pro",
        "gemini-3.0-flash",
    )


def test_browser_agent_intercepts_dangerous_actions() -> None:
    observer = FakeObserver()
    executor = FakeExecutor()
    decider = FakeDecider(
        {"actions": [{"action": "type", "selector": "#cmd", "text": "rm -rf /"}]}
    )

    agent = BrowserAgent(observer=observer, decider=decider, executor=executor)

    with pytest.raises(DangerousActionError):
        agent.run_sync("do not run dangerous action", steps=1)

    assert executor.actions == []


def test_high_risk_action_requires_confirmation_when_not_confirmed() -> None:
    observer = FakeObserver()
    executor = FakeExecutor()
    decider = FakeDecider(
        {"actions": [{"action": "click", "selector": "button.delete-account"}]}
    )

    agent = BrowserAgent(
        observer=observer,
        decider=decider,
        executor=executor,
        confirm_action=lambda action, step_id, run_id: False,
    )

    with pytest.raises(ConfirmationRequiredError):
        agent.run_sync("delete account", steps=1)

    assert executor.actions == []


def test_high_risk_action_runs_when_confirmed() -> None:
    observer = FakeObserver()
    executor = FakeExecutor()
    decider = FakeDecider(
        {"actions": [{"action": "click", "selector": "button.delete-account"}]}
    )

    agent = BrowserAgent(
        observer=observer,
        decider=decider,
        executor=executor,
        confirm_action=lambda action, step_id, run_id: True,
    )
    results = agent.run_sync("confirm delete account", steps=1)

    assert len(results) == 1
    assert executor.actions == ["click"]


def test_high_risk_action_requires_confirmation_semantics_even_if_confirmed() -> None:
    observer = FakeObserver()
    executor = FakeExecutor()
    decider = FakeDecider(
        {"actions": [{"action": "click", "selector": "button.delete-account"}]}
    )

    agent = BrowserAgent(
        observer=observer,
        decider=decider,
        executor=executor,
        confirm_action=lambda action, step_id, run_id: True,
    )

    with pytest.raises(
        ConfirmationRequiredError, match="Confirmation semantics required"
    ):
        agent.run_sync("delete account", steps=1)

    assert executor.actions == []


def test_policy_engine_denies_action_with_context() -> None:
    observer = FakeObserver()
    executor = FakeExecutor()
    decider = FakeDecider(
        {"actions": [{"action": "click", "selector": "button.transfer"}]}
    )
    agent = BrowserAgent(
        observer=observer,
        decider=decider,
        executor=executor,
        policy_context_resolver=lambda action, objective, observation: {
            "domain": "bank.example.com",
            "operation_intent": "wire transfer to recipient",
        },
    )

    with pytest.raises(PolicyDeniedError):
        agent.run_sync("send transfer", steps=1)

    assert executor.actions == []


def test_policy_engine_allows_low_risk_without_confirmation() -> None:
    observer = FakeObserver()
    executor = FakeExecutor()
    decider = FakeDecider({"actions": [{"action": "wait", "duration_ms": 100}]})
    agent = BrowserAgent(observer=observer, decider=decider, executor=executor)

    results = agent.run_sync("read page status", steps=1)

    assert len(results) == 1
    assert executor.actions == ["wait"]


def test_policy_rule_priority_prefers_higher_priority_rule() -> None:
    engine = BrowserPolicyEngine(
        rules=(
            PolicyRule(
                name="allow_all_clicks",
                decision=PolicyDecision.ALLOW,
                matcher=lambda action, context: isinstance(action, ClickAction),
                priority=100,
            ),
            PolicyRule(
                name="deny_delete_clicks",
                decision=PolicyDecision.DENY,
                matcher=lambda action, context: isinstance(action, ClickAction)
                and "delete" in action.selector.lower(),
                priority=200,
            ),
        )
    )

    result = engine.evaluate(
        ClickAction(action="click", selector="button.delete-account")
    )

    assert result.decision is PolicyDecision.DENY
    assert result.rule_name == "deny_delete_clicks"


def test_policy_engine_default_fallback_decision() -> None:
    engine = BrowserPolicyEngine(rules=(), default_decision=PolicyDecision.CONFIRM)
    result = engine.evaluate(WaitAction(action="wait", duration_ms=100))

    assert result.decision is PolicyDecision.CONFIRM
    assert result.rule_name == "default_fallback"


def test_action_requires_confirmation_keeps_backward_compatibility() -> None:
    assert (
        action_requires_confirmation(
            ClickAction(action="click", selector="button.delete-account")
        )
        is True
    )
    assert (
        action_requires_confirmation(WaitAction(action="wait", duration_ms=200))
        is False
    )


def test_retry_policy_retries_then_succeeds_and_emits_audit_fields() -> None:
    class RetryExecutor:
        def __init__(self) -> None:
            self.calls = 0

        def execute(self, action) -> dict[str, object]:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("transient failure")
            return {"ok": True, "attempt": self.calls}

    observer = FakeObserver()
    executor = RetryExecutor()
    decider = FakeDecider({"actions": [{"action": "wait", "duration_ms": 100}]})
    audit_events: list[dict[str, object]] = []

    agent = BrowserAgent(
        observer=observer,
        decider=decider,
        executor=executor,
        max_retries=1,
        audit_logger=audit_events.append,
    )
    results = agent.run_sync("retry once", steps=1)

    assert len(results) == 1
    assert executor.calls == 2
    assert len(audit_events) == 2
    assert audit_events[0]["result"] == "error"
    assert audit_events[0]["retry_count"] == 0
    assert audit_events[1]["result"] == "success"
    assert audit_events[1]["retry_count"] == 1
    for event in audit_events:
        assert set(event.keys()) == {
            "step_id",
            "run_id",
            "action",
            "result",
            "error",
            "retry_count",
            "policy_decision",
            "policy_rule",
        }


def test_audit_log_redacts_sensitive_typed_input() -> None:
    observer = FakeObserver()
    decider = FakeDecider(
        {"actions": [{"action": "type", "selector": "#otp", "text": "123456"}]}
    )
    audit_events: list[dict[str, object]] = []

    class SuccessExecutor:
        def execute(self, action) -> dict[str, object]:
            return {"ok": True}

    agent = BrowserAgent(
        observer=observer,
        decider=decider,
        executor=SuccessExecutor(),
        confirm_action=lambda action, step_id, run_id: True,
        audit_logger=audit_events.append,
    )
    agent.run_sync("confirm type otp", steps=1)

    assert len(audit_events) == 1
    event_action = audit_events[0]["action"]
    assert isinstance(event_action, dict)
    assert event_action["action"] == "type"
    assert event_action["selector"] == "#otp"
    assert event_action["text"] == "[REDACTED]"
    assert event_action["input_redacted"] is True


def test_high_risk_side_effect_action_does_not_blind_retry() -> None:
    class FailingExecutor:
        def __init__(self) -> None:
            self.calls = 0

        def execute(self, action) -> dict[str, object]:
            self.calls += 1
            raise RuntimeError("submit failed")

    observer = FakeObserver()
    executor = FailingExecutor()
    decider = FakeDecider(
        {"actions": [{"action": "click", "selector": "button.submit-order"}]}
    )
    agent = BrowserAgent(
        observer=observer,
        decider=decider,
        executor=executor,
        max_retries=3,
        confirm_action=lambda action, step_id, run_id: True,
    )

    with pytest.raises(RuntimeError, match="submit failed"):
        agent.run_sync("confirm submit order", steps=1)

    assert executor.calls == 1


def test_timeout_policy_raises_timeout_error() -> None:
    class SlowExecutor:
        async def execute(self, action) -> dict[str, object]:
            await asyncio.sleep(0.05)
            return {"ok": True}

    observer = FakeObserver()
    decider = FakeDecider({"actions": [{"action": "wait", "duration_ms": 100}]})
    agent = BrowserAgent(
        observer=observer,
        decider=decider,
        executor=SlowExecutor(),
        action_timeout_seconds=0.001,
    )

    with pytest.raises(asyncio.TimeoutError):
        agent.run_sync("should timeout", steps=1)


def test_goal_checker_stops_run_early() -> None:
    observer = FakeObserver()
    executor = FakeExecutor()
    decider = FakeDecider({"actions": [{"action": "wait", "duration_ms": 100}]})
    agent = BrowserAgent(
        observer=observer,
        decider=decider,
        executor=executor,
        goal_checker=lambda objective, observation, step_index, run_id: step_index >= 0,
    )

    results = agent.run_sync("reach goal quickly", steps=3)

    assert len(results) == 1
    assert results[0].goal_reached is True
    assert decider.calls == 1

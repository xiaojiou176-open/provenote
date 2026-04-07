"""Action schema, parsing, and safety filtering for browser automation."""

from __future__ import annotations

import json
import re
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, ValidationError

from packages.core.ai.model_strategy import GEMINI_COMPUTER_USE_MODEL

DEFAULT_BROWSER_AGENT_MODEL = GEMINI_COMPUTER_USE_MODEL

_DANGEROUS_TOKENS = (
    "javascript:",
    "file://",
    "devtools://",
    "chrome://",
    "data:text/html",
    "rm -rf",
    "drop table",
)


class ActionPlanError(ValueError):
    """Base error for browser action planning."""


class ActionParseError(ActionPlanError):
    """Raised when model output cannot be parsed into valid whitelisted actions."""


class DangerousActionError(ActionPlanError):
    """Raised when parsed actions include unsafe behavior."""


class ClickAction(BaseModel):
    action: Literal["click"]
    selector: str = Field(min_length=1, max_length=1024)


class TypeAction(BaseModel):
    action: Literal["type"]
    selector: str = Field(min_length=1, max_length=1024)
    text: str = Field(min_length=1, max_length=4000)


class ScrollAction(BaseModel):
    action: Literal["scroll"]
    direction: Literal["up", "down"] = "down"
    amount: int = Field(default=600, ge=1, le=5000)


class WaitAction(BaseModel):
    action: Literal["wait"]
    duration_ms: int = Field(default=1000, ge=50, le=30000)


BrowserAction = Annotated[
    Union[ClickAction, TypeAction, ScrollAction, WaitAction],
    Field(discriminator="action"),
]


class BrowserActionPlan(BaseModel):
    actions: list[BrowserAction] = Field(min_length=1, max_length=20)


def _extract_json_candidate(raw_text: str) -> Any:
    text = raw_text.strip()
    if not text:
        raise ActionParseError("Model output is empty")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    inline_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if inline_match:
        return json.loads(inline_match.group(1))

    raise ActionParseError("Model output does not contain valid JSON")


def _normalize_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list):
        return {"actions": payload}
    if isinstance(payload, dict):
        return payload
    raise ActionParseError(f"Unsupported payload type: {type(payload).__name__}")


def parse_action_plan(
    raw_output: str | dict[str, Any] | list[dict[str, Any]],
) -> BrowserActionPlan:
    """Parse model output into validated whitelisted browser actions."""
    payload: Any
    if isinstance(raw_output, str):
        payload = _extract_json_candidate(raw_output)
    else:
        payload = raw_output

    normalized = _normalize_payload(payload)
    try:
        return BrowserActionPlan.model_validate(normalized)
    except ValidationError as exc:
        raise ActionParseError(f"Invalid action schema: {exc}") from exc


def _string_contains_dangerous_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in _DANGEROUS_TOKENS)


def _is_action_safe(action: BrowserAction) -> bool:
    if isinstance(action, (ClickAction, TypeAction)):
        if _string_contains_dangerous_token(action.selector):
            return False
    if isinstance(action, TypeAction):
        if _string_contains_dangerous_token(action.text):
            return False
    return True


def ensure_actions_safe(plan: BrowserActionPlan) -> None:
    """Raise if the plan contains any unsafe action payload."""
    for idx, action in enumerate(plan.actions):
        if not _is_action_safe(action):
            raise DangerousActionError(
                f"Unsafe action rejected at index {idx}: {action.model_dump(mode='json')}"
            )


def action_requires_confirmation(
    action: BrowserAction, context: dict[str, Any] | None = None
) -> bool:
    """Backward-compatible high-risk check powered by policy engine."""
    from packages.core.automation.policy_engine import (
        BrowserPolicyEngine,
        PolicyDecision,
    )

    policy_result = BrowserPolicyEngine().evaluate(action, context=context)
    return policy_result.decision is PolicyDecision.CONFIRM


__all__ = [
    "ActionParseError",
    "ActionPlanError",
    "BrowserAction",
    "BrowserActionPlan",
    "ClickAction",
    "DEFAULT_BROWSER_AGENT_MODEL",
    "DangerousActionError",
    "ScrollAction",
    "TypeAction",
    "WaitAction",
    "action_requires_confirmation",
    "ensure_actions_safe",
    "parse_action_plan",
]

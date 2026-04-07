from __future__ import annotations

from packages.core.automation.browser_actions import ClickAction, WaitAction
from packages.core.automation.policy_engine import (
    BrowserPolicyEngine,
    PolicyDecision,
    has_confirmation_semantics,
    is_high_risk_action,
)


def test_browser_policy_engine_defaults_to_fail_safe_confirmation() -> None:
    engine = BrowserPolicyEngine(rules=())
    result = engine.evaluate(WaitAction(action="wait", duration_ms=100))

    assert result.decision is PolicyDecision.CONFIRM
    assert result.rule_name == "default_fallback"


def test_is_high_risk_action_detects_destructive_clicks() -> None:
    action = ClickAction(action="click", selector="button.delete-account")

    assert is_high_risk_action(action, {"operation_intent": "delete account"}) is True
    assert is_high_risk_action(action, {"operation_intent": "view account"}) is True


def test_has_confirmation_semantics_accepts_keyword_or_explicit_flag() -> None:
    assert (
        has_confirmation_semantics({"operation_intent": "confirm transfer now"}) is True
    )
    assert has_confirmation_semantics({"confirmed_intent": True}) is True
    assert has_confirmation_semantics({"operation_intent": "delete account"}) is False

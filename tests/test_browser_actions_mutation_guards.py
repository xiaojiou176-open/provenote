from typing import Any

import pytest

from packages.core.ai.model_strategy import GEMINI_COMPUTER_USE_MODEL
from packages.core.automation.browser_actions import (
    DEFAULT_BROWSER_AGENT_MODEL,
    ActionParseError,
    DangerousActionError,
    ensure_actions_safe,
    parse_action_plan,
)


def test_default_browser_model_matches_computer_use_strategy() -> None:
    assert DEFAULT_BROWSER_AGENT_MODEL == GEMINI_COMPUTER_USE_MODEL


def test_parse_action_plan_supports_fenced_json_and_applies_defaults() -> None:
    raw = """
    plan:
    ```json
    [
      {"action": "scroll"},
      {"action": "wait"}
    ]
    ```
    """

    plan = parse_action_plan(raw)

    assert len(plan.actions) == 2
    assert plan.actions[0].action == "scroll"
    assert plan.actions[0].amount == 600
    assert plan.actions[1].action == "wait"
    assert plan.actions[1].duration_ms == 1000


def test_parse_action_plan_rejects_non_json_objects() -> None:
    invalid_payload: Any = 123
    with pytest.raises(ActionParseError, match="Unsupported payload type"):
        parse_action_plan(invalid_payload)


def test_ensure_actions_safe_rejects_dangerous_type_payload() -> None:
    plan = parse_action_plan(
        {
            "actions": [
                {"action": "type", "selector": "#query", "text": "DROP TABLE users"}
            ]
        }
    )

    with pytest.raises(DangerousActionError, match="Unsafe action rejected at index 0"):
        ensure_actions_safe(plan)

"""Browser automation primitives for safe structured action execution."""

from packages.core.automation.browser_actions import (
    DEFAULT_BROWSER_AGENT_MODEL,
    ActionParseError,
    ActionPlanError,
    BrowserAction,
    BrowserActionPlan,
    ClickAction,
    DangerousActionError,
    ScrollAction,
    TypeAction,
    WaitAction,
    action_requires_confirmation,
    ensure_actions_safe,
    parse_action_plan,
)
from packages.core.automation.browser_agent import (
    DEFAULT_MODEL_PRIORITY,
    BrowserAgent,
    BrowserStepResult,
    ConfirmationRequiredError,
    PolicyDeniedError,
)
from packages.core.automation.policy_engine import (
    BrowserPolicyEngine,
    PolicyDecision,
    PolicyEvaluationResult,
    PolicyRule,
    build_policy_context,
    default_browser_policy_rules,
)

__all__ = [
    "ActionParseError",
    "ActionPlanError",
    "BrowserAction",
    "BrowserActionPlan",
    "BrowserAgent",
    "BrowserPolicyEngine",
    "BrowserStepResult",
    "ClickAction",
    "DEFAULT_BROWSER_AGENT_MODEL",
    "DEFAULT_MODEL_PRIORITY",
    "DangerousActionError",
    "ConfirmationRequiredError",
    "PolicyDecision",
    "PolicyDeniedError",
    "PolicyEvaluationResult",
    "PolicyRule",
    "ScrollAction",
    "TypeAction",
    "WaitAction",
    "action_requires_confirmation",
    "build_policy_context",
    "default_browser_policy_rules",
    "ensure_actions_safe",
    "parse_action_plan",
]

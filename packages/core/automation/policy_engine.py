"""Policy engine for browser/computer-use action risk decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlparse

from packages.core.automation.browser_actions import (
    BrowserAction,
    ClickAction,
    TypeAction,
)


class PolicyDecision(str, Enum):
    DENY = "deny"
    CONFIRM = "confirm"
    ALLOW = "allow"


PolicyMatcher = Callable[[BrowserAction, Mapping[str, Any]], bool]


@dataclass(frozen=True, slots=True)
class PolicyRule:
    name: str
    decision: PolicyDecision
    matcher: PolicyMatcher
    priority: int = 100
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PolicyEvaluationResult:
    decision: PolicyDecision
    rule_name: str
    priority: int
    reason: str


def _normalize_context(context: Mapping[str, Any] | None) -> dict[str, Any]:
    normalized = dict(context or {})

    domain = normalized.get("domain")
    if isinstance(domain, str) and domain:
        normalized["domain"] = domain.lower()

    operation_intent = normalized.get("operation_intent")
    if isinstance(operation_intent, str) and operation_intent:
        normalized["operation_intent"] = operation_intent.lower()

    risk_level = normalized.get("risk_level")
    if isinstance(risk_level, str) and risk_level:
        normalized["risk_level"] = risk_level.lower()

    return normalized


def build_policy_context(
    *,
    observation: Mapping[str, Any] | None = None,
    operation_intent: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    context = dict(extra or {})
    observed = dict(observation or {})
    context.update(observed)

    if operation_intent and "operation_intent" not in context:
        context["operation_intent"] = operation_intent

    url = observed.get("url")
    if isinstance(url, str) and url and "domain" not in context:
        host = urlparse(url).hostname
        if host:
            context["domain"] = host

    return _normalize_context(context)


def _action_haystacks(action: BrowserAction) -> list[str]:
    haystacks = [action.action.lower()]
    if isinstance(action, (ClickAction, TypeAction)):
        haystacks.append(action.selector.lower())
    if isinstance(action, TypeAction):
        haystacks.append(action.text.lower())
    return haystacks


def _contains_any(haystacks: list[str], tokens: Sequence[str]) -> bool:
    return any(token in text for text in haystacks for token in tokens)


_CONFIRM_TOKENS: tuple[str, ...] = (
    "delete",
    "remove",
    "payment",
    "pay",
    "checkout",
    "submit",
    "send",
    "transfer",
    "wire",
    "purchase",
)

_CONFIRMATION_SEMANTIC_TOKENS: tuple[str, ...] = (
    "confirm",
    "approved",
    "authorize",
    "authorized",
    "consent",
    "i understand",
    "proceed",
)

_DENY_INTENT_TOKENS: tuple[str, ...] = (
    "delete account",
    "close account",
    "confirm transfer",
    "wire transfer",
)

_DENY_DOMAIN_TOKENS: tuple[str, ...] = (
    "bank",
    "wallet",
    "payments",
)


def _deny_critical_destructive(
    action: BrowserAction, context: Mapping[str, Any]
) -> bool:
    risk_level = str(context.get("risk_level", "")).lower()
    if risk_level != "critical":
        return False
    return _contains_any(_action_haystacks(action), _CONFIRM_TOKENS)


def _deny_sensitive_finance_transfer(
    action: BrowserAction, context: Mapping[str, Any]
) -> bool:
    domain = str(context.get("domain", "")).lower()
    operation_intent = str(context.get("operation_intent", "")).lower()
    if not any(token in domain for token in _DENY_DOMAIN_TOKENS):
        return False
    if not any(token in operation_intent for token in _DENY_INTENT_TOKENS):
        return False
    return _contains_any(
        _action_haystacks(action), ("transfer", "wire", "submit", "confirm")
    )


def _confirm_high_risk_action(
    action: BrowserAction, context: Mapping[str, Any]
) -> bool:
    _ = context
    return _contains_any(_action_haystacks(action), _CONFIRM_TOKENS)


def _allow_read_only_intent(action: BrowserAction, context: Mapping[str, Any]) -> bool:
    operation_intent = str(context.get("operation_intent", "")).lower()
    read_only_intents = ("read", "inspect", "view", "observe")
    return action.action in {"scroll", "wait"} and any(
        token in operation_intent for token in read_only_intents
    )


def _allow_passive_actions(action: BrowserAction, context: Mapping[str, Any]) -> bool:
    _ = context
    return action.action in {"scroll", "wait"}


def is_high_risk_action(
    action: BrowserAction, context: Mapping[str, Any] | None = None
) -> bool:
    normalized_context = _normalize_context(context)
    if _deny_critical_destructive(action, normalized_context):
        return True
    if _deny_sensitive_finance_transfer(action, normalized_context):
        return True
    return _confirm_high_risk_action(action, normalized_context)


def has_confirmation_semantics(context: Mapping[str, Any] | None) -> bool:
    normalized_context = _normalize_context(context)
    operation_intent = str(normalized_context.get("operation_intent", "")).lower()
    explicit_signal = normalized_context.get("confirmed_intent")
    if isinstance(explicit_signal, bool) and explicit_signal:
        return True
    return any(token in operation_intent for token in _CONFIRMATION_SEMANTIC_TOKENS)


def default_browser_policy_rules() -> tuple[PolicyRule, ...]:
    return (
        PolicyRule(
            name="deny_critical_destructive",
            decision=PolicyDecision.DENY,
            matcher=_deny_critical_destructive,
            priority=300,
            reason="critical risk level blocks destructive operations",
        ),
        PolicyRule(
            name="deny_sensitive_finance_transfer",
            decision=PolicyDecision.DENY,
            matcher=_deny_sensitive_finance_transfer,
            priority=250,
            reason="sensitive finance transfer requires out-of-band handling",
        ),
        PolicyRule(
            name="confirm_high_risk_action",
            decision=PolicyDecision.CONFIRM,
            matcher=_confirm_high_risk_action,
            priority=200,
            reason="high-risk action requires explicit confirmation",
        ),
        PolicyRule(
            name="allow_read_only_intent",
            decision=PolicyDecision.ALLOW,
            matcher=_allow_read_only_intent,
            priority=100,
            reason="read-only intent allows non-mutating actions",
        ),
        PolicyRule(
            name="allow_passive_actions",
            decision=PolicyDecision.ALLOW,
            matcher=_allow_passive_actions,
            priority=90,
            reason="passive actions are allowed by default",
        ),
    )


class BrowserPolicyEngine:
    def __init__(
        self,
        *,
        rules: Sequence[PolicyRule] | None = None,
        default_decision: PolicyDecision = PolicyDecision.CONFIRM,
    ) -> None:
        self.default_decision = default_decision
        self._rules = tuple(
            sorted(
                tuple(rules) if rules is not None else default_browser_policy_rules(),
                key=lambda rule: rule.priority,
                reverse=True,
            )
        )

    def evaluate(
        self, action: BrowserAction, context: Mapping[str, Any] | None = None
    ) -> PolicyEvaluationResult:
        normalized_context = _normalize_context(context)
        for rule in self._rules:
            if rule.matcher(action, normalized_context):
                return PolicyEvaluationResult(
                    decision=rule.decision,
                    rule_name=rule.name,
                    priority=rule.priority,
                    reason=rule.reason or rule.name,
                )

        return PolicyEvaluationResult(
            decision=self.default_decision,
            rule_name="default_fallback",
            priority=-1,
            reason="no matching rule",
        )


__all__ = [
    "BrowserPolicyEngine",
    "PolicyDecision",
    "PolicyEvaluationResult",
    "PolicyRule",
    "build_policy_context",
    "default_browser_policy_rules",
    "has_confirmation_semantics",
    "is_high_risk_action",
]

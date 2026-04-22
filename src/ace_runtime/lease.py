"""Core ACE lease validator.

The checker is deliberately small: it validates an action against a lease and
an evidence snapshot. It does not call an LLM and it does not decide whether the
evidence is true. Production systems should protect evidence provenance
separately.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Mapping

Decision = Literal["permit", "defer", "deny"]


@dataclass(frozen=True)
class Predicate:
    """A machine-checkable predicate over an evidence snapshot."""

    field: str
    op: str
    value: Any = None
    message: str = ""


@dataclass(frozen=True)
class Evidence:
    """Structured facts observed by the runtime."""

    facts: Mapping[str, Any]
    snapshot_id: str = ""
    source: str = ""
    observed_at: str = ""
    attested: bool = False


@dataclass(frozen=True)
class Lease:
    """Authorization lease for one proposed side effect."""

    action_id: str
    content_hash: str
    requirements: list[Predicate]
    expires_at: str = ""
    approval_state: str = "approved"
    policy_context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationResult:
    """Result returned by the ACE checker."""

    decision: Decision
    reason_code: str
    message: str
    broken_predicates: list[Predicate] = field(default_factory=list)

    @property
    def is_permit(self) -> bool:
        return self.decision == "permit"


def hash_action(action: Mapping[str, Any] | str) -> str:
    """Return a stable SHA-256 hash for a proposed side effect."""
    if isinstance(action, str):
        payload = action
    else:
        payload = json.dumps(action, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compile_lease(
    action_id: str,
    action: Mapping[str, Any] | str,
    requirements: list[Predicate],
    expires_at: str = "",
    policy_context: Mapping[str, Any] | None = None,
) -> Lease:
    """Build a lease for a specific action and predicate set."""
    return Lease(
        action_id=action_id,
        content_hash=hash_action(action),
        requirements=list(requirements),
        expires_at=expires_at,
        approval_state="approved",
        policy_context=dict(policy_context or {}),
    )


def validate_lease(
    lease: Lease,
    evidence: Evidence,
    action: Mapping[str, Any] | str,
    now: datetime | None = None,
) -> ValidationResult:
    """Validate whether a side effect is still authorized.

    The monotonic safety property is simple: if this function does not return
    `permit`, the side effect should not execute.
    """
    if hash_action(action) != lease.content_hash:
        return ValidationResult(
            decision="deny",
            reason_code="action_hash_mismatch",
            message="The proposed action is not the action covered by this lease.",
        )
    if lease.approval_state != "approved":
        return ValidationResult(
            decision="deny",
            reason_code="approval_not_active",
            message="The approval lease is not active.",
        )
    if lease.expires_at:
        current = now or datetime.now(timezone.utc)
        expiry = datetime.fromisoformat(lease.expires_at)
        if current > expiry:
            return ValidationResult(
                decision="defer",
                reason_code="lease_expired",
                message="The lease expired and must be revalidated.",
            )

    broken = [predicate for predicate in lease.requirements if not evaluate_predicate(predicate, evidence.facts)]
    if broken:
        return ValidationResult(
            decision="deny",
            reason_code="predicate_failed",
            message="One or more lease predicates failed.",
            broken_predicates=broken,
        )
    return ValidationResult(
        decision="permit",
        reason_code="lease_valid",
        message="The action is authorized by the current evidence snapshot.",
    )


def evaluate_predicate(predicate: Predicate, facts: Mapping[str, Any]) -> bool:
    actual = _get_path(facts, predicate.field)
    expected = predicate.value
    op = predicate.op

    if op == "eq":
        return actual == expected
    if op == "neq":
        return actual != expected
    if op == "exists":
        return actual is not None
    if op == "missing":
        return actual is None
    if op == "contains":
        return str(expected).lower() in str(actual or "").lower()
    if op == "not_contains":
        return str(expected).lower() not in str(actual or "").lower()
    if op == "regex":
        return bool(re.search(str(expected), str(actual or ""), flags=re.IGNORECASE))
    if op == "not_regex":
        return not bool(re.search(str(expected), str(actual or ""), flags=re.IGNORECASE))
    if op == "in":
        if isinstance(actual, list):
            return any(item in expected for item in actual)
        return actual in expected
    if op == "not_in":
        if isinstance(actual, list):
            return all(item not in expected for item in actual)
        return actual not in expected
    if op == "gte":
        return _as_float(actual) >= _as_float(expected)
    if op == "lte":
        return _as_float(actual) <= _as_float(expected)
    raise ValueError(f"Unsupported predicate operator: {op}")


def lease_to_dict(lease: Lease) -> dict[str, Any]:
    return asdict(lease)


def result_to_dict(result: ValidationResult) -> dict[str, Any]:
    return asdict(result)


def lease_from_dict(payload: Mapping[str, Any]) -> Lease:
    return Lease(
        action_id=str(payload["action_id"]),
        content_hash=str(payload["content_hash"]),
        requirements=[Predicate(**item) for item in payload.get("requirements", [])],
        expires_at=str(payload.get("expires_at", "")),
        approval_state=str(payload.get("approval_state", "approved")),
        policy_context=dict(payload.get("policy_context", {})),
    )


def evidence_from_dict(payload: Mapping[str, Any]) -> Evidence:
    return Evidence(
        facts=dict(payload.get("facts", payload)),
        snapshot_id=str(payload.get("snapshot_id", "")),
        source=str(payload.get("source", "")),
        observed_at=str(payload.get("observed_at", "")),
        attested=bool(payload.get("attested", False)),
    )


def _get_path(facts: Mapping[str, Any], path: str) -> Any:
    current: Any = facts
    for part in path.split("."):
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            return None
    return current


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")

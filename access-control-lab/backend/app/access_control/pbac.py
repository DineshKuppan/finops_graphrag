"""Policy-Based Access Control (PBAC).

Generalizes RBAC and ABAC: every rule is a *declarative policy
document* (loaded from JSON, not hard-coded in Python) that matches on
subject attributes, resource attributes, roles, AND environment/context
(e.g. time of day). Multiple policies can match the same request; a
deny-overrides combining algorithm resolves conflicts, and everything
not explicitly permitted is denied by default.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.resource import Invoice
from app.models.user import User

_POLICY_FILE = Path(__file__).parent / "policies" / "finops_policies.json"

with open(_POLICY_FILE) as f:
    POLICIES: list[dict] = json.load(f)

_OPERATORS = {
    "eq": lambda a, b: a == b,
    "neq": lambda a, b: a != b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "contains": lambda a, b: b in a if isinstance(a, (list, tuple, set, str)) else False,
    "in": lambda a, b: a in b,
}


def build_environment(simulate_after_hours: bool = False) -> dict:
    now = datetime.now(timezone.utc)
    business_hours = 13 <= now.hour < 21  # ~09:00-17:00 US Eastern, in UTC
    if simulate_after_hours:
        business_hours = False
    return {
        "utc_hour": now.hour,
        "business_hours": business_hours,
        "simulated": simulate_after_hours,
    }


def _resolve_path(context: dict[str, Any], path: str) -> Any:
    value: Any = context
    for part in path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = getattr(value, part, None)
    return value


def _condition_matches(condition: dict, context: dict) -> bool:
    actual = _resolve_path(context, condition["attr"])
    expected = condition["value"] if "value" in condition else _resolve_path(context, condition["value_ref"])
    op = _OPERATORS[condition["op"]]
    try:
        return bool(op(actual, expected))
    except TypeError:
        return False


def _build_context(user: User, invoice: Invoice, environment: dict) -> dict:
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "roles": user.roles,
            "department": user.department,
            "clearance_level": user.clearance_level,
            "region": user.region,
        },
        "resource": {
            "id": invoice.id,
            "department": invoice.department,
            "amount": invoice.amount,
            "classification": invoice.classification,
            "classification_level": invoice.classification_level,
            "region": invoice.region,
        },
        "environment": environment,
    }


def evaluate_pbac(user: User, invoice: Invoice, action: str, environment: dict | None = None) -> dict:
    environment = environment if environment is not None else build_environment()
    context = _build_context(user, invoice, environment)

    trace: list[str] = [f"environment = {environment}"]
    permits: list[str] = []
    denies: list[str] = []

    for policy in POLICIES:
        if action not in policy["actions"]:
            continue
        matched = all(_condition_matches(c, context) for c in policy["conditions"])
        trace.append(
            f"policy '{policy['id']}' ({policy['effect']}) -> "
            f"{'MATCH' if matched else 'no match'}"
        )
        if matched:
            (permits if policy["effect"] == "permit" else denies).append(policy["id"])

    if denies:
        return {
            "allowed": False,
            "model": "PBAC",
            "action": action,
            "reason": f"Deny-overrides: policy/policies {denies} explicitly deny '{action}'.",
            "trace": trace,
        }
    if permits:
        return {
            "allowed": True,
            "model": "PBAC",
            "action": action,
            "reason": f"Policy/policies {permits} permit '{action}', and no policy denies it.",
            "trace": trace,
        }
    return {
        "allowed": False,
        "model": "PBAC",
        "action": action,
        "reason": "Default deny: no policy explicitly permitted this action.",
        "trace": trace,
    }

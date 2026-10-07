"""Attribute-Based Access Control (ABAC).

Decisions are computed from *attributes* of the subject (department,
clearance level, region) and the resource (department, classification,
amount) -- no role lookup table involved. The same role can get
different answers on different invoices, which is the capability RBAC
lacks.
"""

from app.models.resource import Invoice
from app.models.user import User

APPROVAL_BUDGET_PER_CLEARANCE_LEVEL = 50_000


def evaluate_abac(user: User, invoice: Invoice, action: str) -> dict:
    trace = [
        f"user.department={user.department!r} vs invoice.department={invoice.department!r}",
        f"user.clearance_level={user.clearance_level} vs invoice.classification_level={invoice.classification_level} ({invoice.classification})",
        f"user.region={user.region!r} vs invoice.region={invoice.region!r}",
    ]

    if "admin" in user.roles:
        trace.append("user has the 'admin' role attribute -> unconditional access")
        return _allow(action, trace, "Subject attribute 'role=admin' grants full access.")

    same_department = user.department == invoice.department
    sufficient_clearance = user.clearance_level >= invoice.classification_level
    same_region = user.region == invoice.region

    if action == "view_invoice":
        if same_department:
            return _allow(action, trace, "Subject and resource share the same department attribute.")
        if sufficient_clearance and same_region:
            return _allow(
                action,
                trace,
                "Subject's clearance_level meets the resource's classification_level, "
                "and region attributes match.",
            )
        return _deny(
            action,
            trace,
            "Neither department match nor (sufficient clearance + matching region) holds.",
        )

    if action == "approve_invoice":
        budget = user.clearance_level * APPROVAL_BUDGET_PER_CLEARANCE_LEVEL
        trace.append(
            f"approval budget = clearance_level({user.clearance_level}) * "
            f"{APPROVAL_BUDGET_PER_CLEARANCE_LEVEL} = {budget}; invoice.amount={invoice.amount}"
        )
        if same_department and sufficient_clearance and invoice.amount <= budget:
            return _allow(
                action,
                trace,
                "Same department, sufficient clearance for the classification, "
                "and amount is within the subject's clearance-derived budget.",
            )
        return _deny(
            action,
            trace,
            "Department, clearance/classification, or amount-vs-budget check failed.",
        )

    return _deny(action, trace, f"Unknown action '{action}'.")


def _allow(action: str, trace: list[str], reason: str) -> dict:
    return {"allowed": True, "model": "ABAC", "action": action, "reason": reason, "trace": trace}


def _deny(action: str, trace: list[str], reason: str) -> dict:
    return {"allowed": False, "model": "ABAC", "action": action, "reason": reason, "trace": trace}

"""Role-Based Access Control (RBAC).

A static role -> permission matrix. Decisions depend only on *which
roles* the subject holds -- never on who owns the resource, what
department it belongs to, or any other attribute. That rigidity is the
point of this module: it is what ABAC/PBAC are built to fix.
"""

from app.models.resource import Invoice
from app.models.user import User

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {"view_invoice", "approve_invoice"},
    "finance_manager": {"view_invoice", "approve_invoice"},
    "auditor": {"view_invoice"},
    # "employee" intentionally has no invoice permissions under RBAC,
    # even for invoices in their own department -- RBAC has no concept
    # of "own department".
}


def evaluate_rbac(user: User, invoice: Invoice, action: str) -> dict:
    trace = [f"user roles = {user.roles}"]
    for role in user.roles:
        permissions = ROLE_PERMISSIONS.get(role, set())
        trace.append(f"role '{role}' grants {sorted(permissions) or '{}'}")
        if action in permissions:
            return {
                "allowed": True,
                "model": "RBAC",
                "action": action,
                "reason": f"Role '{role}' is granted '{action}' on invoices.",
                "trace": trace,
            }
    return {
        "allowed": False,
        "model": "RBAC",
        "action": action,
        "reason": (
            f"No role held by '{user.username}' grants '{action}'. "
            "RBAC does not consider department, clearance, or ownership."
        ),
        "trace": trace,
    }

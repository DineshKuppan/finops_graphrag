"""In-memory seed data for the lab.

Everything lives in memory and resets on restart -- there is no real
database. Every demo user's password is "password123" (hashed below, not
stored in plaintext) so the lab stays copy-paste simple.
"""

from app.core.security import hash_password
from app.models.resource import Invoice
from app.models.user import User

DEMO_PASSWORD = "password123"
_HASH = hash_password(DEMO_PASSWORD)

USERS: dict[str, User] = {
    u.username: u
    for u in [
        User(
            id="u1",
            username="alice_admin",
            password_hash=_HASH,
            full_name="Alice Nguyen",
            roles=["admin"],
            department="IT",
            clearance_level=5,
            region="US",
        ),
        User(
            id="u2",
            username="bob_finance",
            password_hash=_HASH,
            full_name="Bob Castillo",
            roles=["finance_manager"],
            department="FINANCE",
            clearance_level=3,
            region="US",
        ),
        User(
            id="u3",
            username="carol_auditor",
            password_hash=_HASH,
            full_name="Carol Osei",
            roles=["auditor"],
            department="FINANCE",
            clearance_level=4,
            region="EU",
        ),
        User(
            id="u4",
            username="dave_marketing",
            password_hash=_HASH,
            full_name="Dave Kim",
            roles=["employee"],
            department="MARKETING",
            clearance_level=1,
            region="US",
        ),
        User(
            id="u5",
            username="erin_legal",
            password_hash=_HASH,
            full_name="Erin Walsh",
            roles=["employee"],
            department="LEGAL",
            clearance_level=2,
            region="EU",
        ),
    ]
}

INVOICES: dict[str, Invoice] = {
    inv.id: inv
    for inv in [
        Invoice(
            id="INV-1001",
            title="AWS Cloud Infra - September",
            department="IT",
            amount=45_000,
            classification="internal",
            region="US",
            owner_username="alice_admin",
        ),
        Invoice(
            id="INV-1002",
            title="Datadog Observability Platform",
            department="IT",
            amount=12_000,
            classification="internal",
            region="US",
            owner_username="alice_admin",
        ),
        Invoice(
            id="INV-1003",
            title="Office Lease - NYC HQ",
            department="REALTY",
            amount=250_000,
            classification="confidential",
            region="US",
            owner_username="bob_finance",
        ),
        Invoice(
            id="INV-1004",
            title="Outside Counsel - M&A Advisory",
            department="LEGAL",
            amount=80_000,
            classification="confidential",
            region="EU",
            owner_username="erin_legal",
        ),
        Invoice(
            id="INV-1005",
            title="Q4 Marketing Campaign",
            department="MARKETING",
            amount=30_000,
            classification="internal",
            region="US",
            owner_username="dave_marketing",
        ),
        Invoice(
            id="INV-1006",
            title="Executive Offsite - Restricted Budget",
            department="FINANCE",
            amount=120_000,
            classification="restricted",
            region="US",
            owner_username="bob_finance",
        ),
        Invoice(
            id="INV-1007",
            title="Payroll Processing Fees",
            department="FINANCE",
            amount=15_000,
            classification="internal",
            region="US",
            owner_username="bob_finance",
        ),
    ]
}


def get_user(username: str) -> User | None:
    return USERS.get(username)


def list_invoices() -> list[Invoice]:
    return list(INVOICES.values())


def get_invoice(invoice_id: str) -> Invoice | None:
    return INVOICES.get(invoice_id)

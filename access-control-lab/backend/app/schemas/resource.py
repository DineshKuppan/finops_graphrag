from pydantic import BaseModel


class InvoiceOut(BaseModel):
    id: str
    title: str
    department: str
    amount: float
    classification: str
    classification_level: int
    region: str
    owner_username: str


class Decision(BaseModel):
    """A uniform shape for RBAC/ABAC/PBAC decisions so the frontend can
    render all three models with one component."""

    allowed: bool
    model: str  # "RBAC" | "ABAC" | "PBAC"
    action: str
    reason: str
    trace: list[str] = []


class InvoiceDecision(BaseModel):
    invoice: InvoiceOut
    decision: Decision

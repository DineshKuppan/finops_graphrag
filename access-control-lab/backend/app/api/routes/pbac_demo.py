from fastapi import APIRouter, Depends, HTTPException

from app.access_control.pbac import POLICIES, build_environment, evaluate_pbac
from app.api.deps import get_current_user
from app.db.seed_data import get_invoice, list_invoices
from app.models.user import User
from app.schemas.resource import Decision, InvoiceDecision, InvoiceOut

router = APIRouter(prefix="/pbac", tags=["pbac"])


@router.get("/policies")
def list_policies():
    """Exposes the raw policy documents so the frontend can show the
    actual declarative rules being evaluated, not just the outcome."""
    return POLICIES


@router.get("/invoices", response_model=list[InvoiceDecision])
def view_invoices(
    simulate_after_hours: bool = False,
    current_user: User = Depends(get_current_user),
):
    environment = build_environment(simulate_after_hours=simulate_after_hours)
    results = []
    for invoice in list_invoices():
        decision = evaluate_pbac(current_user, invoice, "view_invoice", environment)
        results.append(
            InvoiceDecision(invoice=InvoiceOut(**invoice.public_view()), decision=Decision(**decision))
        )
    return results


@router.post("/invoices/{invoice_id}/approve", response_model=InvoiceDecision)
def approve_invoice(
    invoice_id: str,
    simulate_after_hours: bool = False,
    current_user: User = Depends(get_current_user),
):
    invoice = get_invoice(invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    environment = build_environment(simulate_after_hours=simulate_after_hours)
    decision = evaluate_pbac(current_user, invoice, "approve_invoice", environment)
    return InvoiceDecision(invoice=InvoiceOut(**invoice.public_view()), decision=Decision(**decision))

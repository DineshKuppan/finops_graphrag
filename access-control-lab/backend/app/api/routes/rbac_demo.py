from fastapi import APIRouter, Depends, HTTPException

from app.access_control.rbac import evaluate_rbac
from app.api.deps import get_current_user
from app.db.seed_data import get_invoice, list_invoices
from app.models.user import User
from app.schemas.resource import Decision, InvoiceDecision, InvoiceOut

router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.get("/invoices", response_model=list[InvoiceDecision])
def view_invoices(current_user: User = Depends(get_current_user)):
    results = []
    for invoice in list_invoices():
        decision = evaluate_rbac(current_user, invoice, "view_invoice")
        results.append(
            InvoiceDecision(invoice=InvoiceOut(**invoice.public_view()), decision=Decision(**decision))
        )
    return results


@router.post("/invoices/{invoice_id}/approve", response_model=InvoiceDecision)
def approve_invoice(invoice_id: str, current_user: User = Depends(get_current_user)):
    invoice = get_invoice(invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    decision = evaluate_rbac(current_user, invoice, "approve_invoice")
    return InvoiceDecision(invoice=InvoiceOut(**invoice.public_view()), decision=Decision(**decision))

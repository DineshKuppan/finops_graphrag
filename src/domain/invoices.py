from typing import Optional
from pydantic import BaseModel
from src.domain.base import Party

class Invoice(BaseModel):
    invoice_number: str
    vendor: Party
    amount: float
    currency: str = "USD"
    bill_to: Optional[Party] = None
    issue_date: Optional[str] = None  # ISO-8601, e.g. "2026-01-31"
    contract_ref: Optional[str] = None  # ULID of the governing contract
    payment_method: Optional[str] = None  # e.g., ACH, Wire, Credit Card
    remit_to_account: Optional[str] = None

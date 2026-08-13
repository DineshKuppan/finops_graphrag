from typing import List, Optional
from pydantic import BaseModel

class ForceMajeure(BaseModel):
    trigger: str
    suspension_days: int

class SecurityDeposit(BaseModel):
    amount: float
    refund_terms: str
    force_majeure: Optional[ForceMajeure] = None

class LiabilityCap(BaseModel):
    amount: float
    basis: str  # e.g., "12 months fees", "Fixed multiplier"
    exclusions: List[str]
    security_deposit: Optional[SecurityDeposit] = None

class PaymentSchedule(BaseModel):
    frequency: str  # e.g., Monthly, Net-30, Annual
    due_day: int
    method: str  # e.g., ACH, Wire, Credit Card
    liability_cap: Optional[LiabilityCap] = None

class FinancialTerm(BaseModel):
    name: str
    value: float
    currency: str = "USD"
    payment_schedule: Optional[PaymentSchedule] = None
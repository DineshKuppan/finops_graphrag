from typing import Optional
from pydantic import BaseModel

class CurePeriod(BaseModel):
    days: int
    remedy_action: str

class LiquidatedDamages(BaseModel):
    cap: float
    daily_rate: float
    currency: str = "USD"
    cure_period: Optional[CurePeriod] = None

class BreachEvent(BaseModel):
    condition: str
    cure_period_days: int
    liquidated_damages: Optional[LiquidatedDamages] = None

class PenaltyClause(BaseModel):
    clause_type: str  # e.g., Late Payment, SLA Breach, Termination Penalty
    trigger: str
    amount: float
    breach_event: Optional[BreachEvent] = None
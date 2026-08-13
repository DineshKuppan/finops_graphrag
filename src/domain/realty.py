from typing import Optional
from pydantic import BaseModel

class RenewalOption(BaseModel):
    notice_by_days: int
    term_months: int
    rent_basis: str  # e.g., "Market Rate", "5% Escalation"

class CAMCharges(BaseModel):
    maintenance_cost: float
    annual_cap: float
    renewal_option: Optional[RenewalOption] = None

class Premises(BaseModel):
    floor: str
    unit: str
    fit_out_status: str  # e.g., "Fully Furnished", "Shell & Core"
    cam_charges: Optional[CAMCharges] = None

class RentSchedule(BaseModel):
    base_rent: float
    escalation_percentage: float
    period: str  # e.g., Monthly, Quarterly
    premises: Optional[Premises] = None

class LeaseTerm(BaseModel):
    start_date: str
    end_date: str
    area_sqft: float
    rent_schedule: Optional[RentSchedule] = None
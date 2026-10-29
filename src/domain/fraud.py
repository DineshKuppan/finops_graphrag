from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

Severity = Literal["LOW", "MEDIUM", "HIGH"]

# --- Read-only snapshot the fraud rules evaluate (storage-agnostic) ---

class PartyRecord(BaseModel):
    party_id: str
    names: List[str]  # first-seen name, then every other variant resolved onto this party
    tax_ids: List[str] = Field(default_factory=list)
    bank_accounts: List[str] = Field(default_factory=list)

class LeaseRecord(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    floor: Optional[str] = None
    unit: Optional[str] = None

class ContractRecord(BaseModel):
    contract_id: str
    title: str
    status: str
    party_roles: Dict[str, str] = Field(default_factory=dict)  # party_id -> role
    declared_accounts: Dict[str, List[str]] = Field(default_factory=dict)  # party_id -> accounts declared here
    term_values: List[float] = Field(default_factory=list)
    payment_methods: List[str] = Field(default_factory=list)
    leases: List[LeaseRecord] = Field(default_factory=list)

class InvoiceRecord(BaseModel):
    invoice_id: str
    invoice_number: str
    source_doc_id: str
    vendor_id: str
    bill_to_id: Optional[str] = None
    amount: float
    currency: str
    issue_date: Optional[str] = None
    contract_ref: Optional[str] = None
    payment_method: Optional[str] = None
    remit_to_account: Optional[str] = None

class FraudGraphSnapshot(BaseModel):
    parties: Dict[str, PartyRecord] = Field(default_factory=dict)
    contracts: Dict[str, ContractRecord] = Field(default_factory=dict)
    invoices: List[InvoiceRecord] = Field(default_factory=list)

    def display_name(self, party_id: str) -> str:
        party = self.parties.get(party_id)
        return party.names[0] if party and party.names else party_id

# --- Detection output ---

class FraudSignal(BaseModel):
    rule_id: str  # e.g. "SHARED_BANK_ACCOUNT"
    severity: Severity
    entity_ids: List[str]  # graph nodes implicated
    evidence: str  # human-readable reason; identifiers are masked
    source_doc_ids: List[str] = Field(default_factory=list)  # traceability to ingested documents

class RiskReport(BaseModel):
    entity_id: str
    entity_type: Literal["Party", "Contract", "Invoice", "Unknown"]
    score: float  # 0..1, noisy-OR over signal severities
    signals: List[FraudSignal]

class FraudAssessment(BaseModel):
    signals: List[FraudSignal]
    reports: List[RiskReport]  # highest risk first
    explanation_prompt: str

# --- Reviewer feedback (closes the loop on signal precision) ---

class ReviewFeedback(BaseModel):
    rule_id: str  # the signal's rule_id, e.g. "DUPLICATE_AMOUNT"
    verdict: Literal["CONFIRMED", "DISMISSED"]
    entity_ids: List[str] = Field(default_factory=list)
    reviewer: Optional[str] = None
    note: Optional[str] = None
    recorded_at: str  # ISO-8601 timestamp

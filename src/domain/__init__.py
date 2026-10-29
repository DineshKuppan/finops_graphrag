from pydantic import BaseModel, Field
from typing import List
from src.domain.base import MetaContext, Party, Clause
from src.domain.penalties import PenaltyClause
from src.domain.realty import LeaseTerm
from src.domain.financials import FinancialTerm
from src.domain.invoices import Invoice

class FinOpsContractGraph(BaseModel):
    ulid: str
    title: str
    status: str
    context: MetaContext
    parties: List[Party] = Field(default_factory=list)
    clauses: List[Clause] = Field(default_factory=list)
    
    # Domain Ontologies
    penalty_clauses: List[PenaltyClause] = Field(default_factory=list)
    lease_terms: List[LeaseTerm] = Field(default_factory=list)
    financial_terms: List[FinancialTerm] = Field(default_factory=list)
    invoices: List[Invoice] = Field(default_factory=list)

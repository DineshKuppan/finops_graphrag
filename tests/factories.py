"""Builders for realistic documents used across the fraud-detection tests."""
from typing import List, Optional

from src.domain import FinOpsContractGraph
from src.domain.base import MetaContext, Party
from src.domain.financials import FinancialTerm, PaymentSchedule
from src.domain.invoices import Invoice
from src.domain.realty import LeaseTerm, Premises, RentSchedule
from src.infrastructure.networkx_repo import NetworkXGraphRepository


def contract(
    ulid: str,
    parties: List[Party],
    terms: Optional[List[FinancialTerm]] = None,
    leases: Optional[List[LeaseTerm]] = None,
    status: str = "Active",
    doc_type: str = "Vendor Contract",
    domain: str = "Subscription",
) -> FinOpsContractGraph:
    return FinOpsContractGraph(
        ulid=ulid, title=f"Doc {ulid}", status=status,
        context=MetaContext(domain=domain, doc_type=doc_type),
        parties=parties, financial_terms=terms or [], lease_terms=leases or [],
    )


def invoice_doc(ulid: str, invoices: List[Invoice]) -> FinOpsContractGraph:
    return FinOpsContractGraph(
        ulid=ulid, title=f"Invoice batch {ulid}", status="Received",
        context=MetaContext(domain="Subscription", doc_type="Invoice"),
        invoices=invoices,
    )


def term(value: float, method: str = "ACH") -> FinancialTerm:
    return FinancialTerm(
        name="Platform Fee", value=value,
        payment_schedule=PaymentSchedule(frequency="Monthly", due_day=1, method=method),
    )


def lease(start: str, end: str, floor: str = "3", unit: str = "301") -> LeaseTerm:
    return LeaseTerm(
        start_date=start, end_date=end, area_sqft=2000,
        rent_schedule=RentSchedule(
            base_rent=9000, escalation_percentage=3, period="Monthly",
            premises=Premises(floor=floor, unit=unit, fit_out_status="Shell & Core"),
        ),
    )


def repo_with(*docs: FinOpsContractGraph) -> NetworkXGraphRepository:
    repo = NetworkXGraphRepository()
    for doc in docs:
        repo.save_contract_graph(doc)
    return repo


BUYER = Party(name="FinOps Corp", role="Customer")

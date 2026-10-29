from collections import defaultdict
from itertools import combinations
from typing import Dict, List
from src.domain.fraud import FraudGraphSnapshot, FraudSignal, InvoiceRecord
from src.interfaces.fraud_rule import IFraudRule
from src.use_cases.fraud_rules._util import parse_iso_date

class DuplicateBillingRule(IFraudRule):
    """Same vendor billing the same invoice number twice, or the same amount within a short
    window, is the most common route to a double payment."""

    def __init__(self, window_days: int = 14):
        self.window_days = window_days

    def evaluate(self, snapshot: FraudGraphSnapshot) -> List[FraudSignal]:
        by_vendor: Dict[str, List[InvoiceRecord]] = defaultdict(list)
        for inv in snapshot.invoices:
            by_vendor[inv.vendor_id].append(inv)

        signals = []
        for vendor_id, invoices in by_vendor.items():
            vendor = snapshot.display_name(vendor_id)
            for a, b in combinations(invoices, 2):
                entities = [a.invoice_id, b.invoice_id, vendor_id]
                docs = sorted({a.source_doc_id, b.source_doc_id})
                if a.invoice_number.strip().lower() == b.invoice_number.strip().lower():
                    signals.append(FraudSignal(
                        rule_id="DUPLICATE_INVOICE_NUMBER", severity="HIGH", entity_ids=entities,
                        evidence=f"{vendor} submitted invoice number {a.invoice_number} more than once",
                        source_doc_ids=docs,
                    ))
                elif self._same_charge_in_window(a, b):
                    signals.append(FraudSignal(
                        rule_id="DUPLICATE_AMOUNT", severity="MEDIUM", entity_ids=entities,
                        evidence=(
                            f"{vendor} billed {a.amount:,.2f} {a.currency} on invoices {a.invoice_number} "
                            f"({a.issue_date}) and {b.invoice_number} ({b.issue_date}), "
                            f"less than {self.window_days} days apart"
                        ),
                        source_doc_ids=docs,
                    ))
        return signals

    def _same_charge_in_window(self, a: InvoiceRecord, b: InvoiceRecord) -> bool:
        if a.currency != b.currency or abs(a.amount - b.amount) >= 0.005:
            return False
        date_a, date_b = parse_iso_date(a.issue_date), parse_iso_date(b.issue_date)
        return bool(date_a and date_b) and abs((date_a - date_b).days) < self.window_days

class ContractOverbillingRule(IFraudRule):
    """No single invoice should exceed the largest priced term of the contract it bills under.
    Cumulative billing is out of scope until term duration is modelled (see spec §6)."""

    def __init__(self, tolerance: float = 0.0):
        self.tolerance = tolerance

    def evaluate(self, snapshot: FraudGraphSnapshot) -> List[FraudSignal]:
        signals = []
        for inv in snapshot.invoices:
            contract = snapshot.contracts.get(inv.contract_ref) if inv.contract_ref else None
            if not contract or not contract.term_values:
                continue
            ceiling = max(contract.term_values)
            if inv.amount <= ceiling * (1 + self.tolerance):
                continue
            signals.append(FraudSignal(
                rule_id="CONTRACT_OVERBILLING",
                severity="HIGH" if inv.amount >= 2 * ceiling else "MEDIUM",
                entity_ids=[inv.invoice_id, contract.contract_id, inv.vendor_id],
                evidence=(
                    f"Invoice {inv.invoice_number} for {inv.amount:,.2f} {inv.currency} exceeds the largest "
                    f"priced term ({ceiling:,.2f}) of contract '{contract.title}'"
                ),
                source_doc_ids=sorted({inv.source_doc_id, contract.contract_id}),
            ))
        return signals

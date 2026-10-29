from collections import defaultdict
from itertools import combinations
from typing import Dict, List
from src.domain.fraud import FraudGraphSnapshot, FraudSignal, InvoiceRecord
from src.interfaces.fraud_rule import IFraudRule
from src.use_cases.fraud_rules._util import mask, parse_iso_date

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

_INACTIVE_STATUSES = {"terminated", "expired", "cancelled", "canceled", "void", "inactive", "suspended"}

class OrphanInvoiceRule(IFraudRule):
    """Invoices must bill under a live contract the vendor is actually party to; anything else
    is unauthorised or fabricated billing."""

    def evaluate(self, snapshot: FraudGraphSnapshot) -> List[FraudSignal]:
        signals = []
        for inv in snapshot.invoices:
            vendor = snapshot.display_name(inv.vendor_id)
            contract = snapshot.contracts.get(inv.contract_ref) if inv.contract_ref else None
            if not inv.contract_ref:
                severity, reason = "MEDIUM", "references no governing contract"
            elif contract is None:
                severity, reason = "HIGH", f"references contract {inv.contract_ref}, which is not in the graph"
            elif contract.status.strip().lower() in _INACTIVE_STATUSES:
                severity, reason = "HIGH", f"bills under contract '{contract.title}' whose status is {contract.status}"
            elif inv.vendor_id not in contract.party_roles:
                severity, reason = "HIGH", f"bills under contract '{contract.title}', to which {vendor} is not a party"
            else:
                continue
            signals.append(FraudSignal(
                rule_id="ORPHAN_INVOICE", severity=severity, entity_ids=[inv.invoice_id, inv.vendor_id],
                evidence=f"Invoice {inv.invoice_number} from {vendor} {reason}",
                source_doc_ids=sorted({inv.source_doc_id} | ({contract.contract_id} if contract else set())),
            ))
        return signals

class PaymentDriftRule(IFraudRule):
    """An invoice asking to be paid differently from what the contract agreed — especially into
    a new bank account — is the signature of payment-redirection (BEC) fraud."""

    def evaluate(self, snapshot: FraudGraphSnapshot) -> List[FraudSignal]:
        signals = []
        for inv in snapshot.invoices:
            contract = snapshot.contracts.get(inv.contract_ref) if inv.contract_ref else None
            if not contract:
                continue
            entities = [inv.invoice_id, contract.contract_id, inv.vendor_id]
            docs = sorted({inv.source_doc_id, contract.contract_id})

            agreed_methods = {m.strip().lower() for m in contract.payment_methods}
            if inv.payment_method and agreed_methods and inv.payment_method.strip().lower() not in agreed_methods:
                signals.append(FraudSignal(
                    rule_id="PAYMENT_METHOD_DRIFT", severity="MEDIUM", entity_ids=entities,
                    evidence=(
                        f"Invoice {inv.invoice_number} requests payment by {inv.payment_method}; contract "
                        f"'{contract.title}' agrees {', '.join(sorted(set(contract.payment_methods)))}"
                    ),
                    source_doc_ids=docs,
                ))

            declared = contract.declared_accounts.get(inv.vendor_id)
            if inv.remit_to_account and declared and inv.remit_to_account not in declared:
                signals.append(FraudSignal(
                    rule_id="REMITTANCE_ACCOUNT_DRIFT", severity="HIGH", entity_ids=entities,
                    evidence=(
                        f"Invoice {inv.invoice_number} remits to account {mask(inv.remit_to_account)}, but contract "
                        f"'{contract.title}' declares {', '.join(mask(a) for a in declared)} for "
                        f"{snapshot.display_name(inv.vendor_id)}"
                    ),
                    source_doc_ids=docs,
                ))
        return signals

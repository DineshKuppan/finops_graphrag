from collections import defaultdict
from typing import Dict, List, Set, Tuple
from src.domain.fraud import FraudGraphSnapshot, FraudSignal
from src.interfaces.fraud_rule import IFraudRule
from src.use_cases.fraud_rules._util import docs_mentioning, mask

class SharedIdentifierRule(IFraudRule):
    """Distinct parties resolving to one tax ID or bank account is the classic shell-vendor
    pattern: a single beneficiary hiding behind several vendor names."""

    def evaluate(self, snapshot: FraudGraphSnapshot) -> List[FraudSignal]:
        owners: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        for party in snapshot.parties.values():
            for tax_id in party.tax_ids:
                owners[("SHARED_TAX_ID", tax_id)].add(party.party_id)
            for account in party.bank_accounts:
                owners[("SHARED_BANK_ACCOUNT", account)].add(party.party_id)
        # An invoice asking to be paid into an account ties that account to its vendor too
        for inv in snapshot.invoices:
            if inv.remit_to_account:
                owners[("SHARED_BANK_ACCOUNT", inv.remit_to_account)].add(inv.vendor_id)

        signals = []
        for (rule_id, value), party_ids in owners.items():
            if len(party_ids) < 2:
                continue
            ordered = sorted(party_ids)
            kind = "tax ID" if rule_id == "SHARED_TAX_ID" else "bank account"
            names = ", ".join(snapshot.display_name(p) for p in ordered)
            signals.append(FraudSignal(
                rule_id=rule_id, severity="HIGH", entity_ids=ordered,
                evidence=f"{len(ordered)} distinct parties ({names}) share {kind} {mask(value)}",
                source_doc_ids=docs_mentioning(snapshot, ordered),
            ))
        return signals

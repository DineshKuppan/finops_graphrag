from dataclasses import dataclass
from datetime import date
from itertools import combinations
from typing import FrozenSet, List
from src.domain.fraud import FraudGraphSnapshot, FraudSignal
from src.domain.identity import canonical_identifier
from src.interfaces.fraud_rule import IFraudRule
from src.use_cases.fraud_rules._util import parse_iso_date

_LANDLORD_ROLES = ("landlord", "lessor")

@dataclass(frozen=True)
class _LeaseWindow:
    contract_id: str
    title: str
    landlords: FrozenSet[str]
    premises: str
    start: date
    end: date

class LeaseOverlapRule(IFraudRule):
    """The same landlord leasing the same unit under two contracts for overlapping dates means
    the space is paid for twice, or one lease is a phantom. Leases without premises or a
    landlord are skipped: without a building address, guessing would only add noise."""

    def evaluate(self, snapshot: FraudGraphSnapshot) -> List[FraudSignal]:
        windows = []
        for contract in snapshot.contracts.values():
            landlords = frozenset(
                pid for pid, role in contract.party_roles.items()
                if any(keyword in role.lower() for keyword in _LANDLORD_ROLES)
            )
            if not landlords:
                continue
            for lease in contract.leases:
                start, end = parse_iso_date(lease.start_date), parse_iso_date(lease.end_date)
                if start and end and lease.floor and lease.unit:
                    premises = f"floor {canonical_identifier(lease.floor)} unit {canonical_identifier(lease.unit)}"
                    windows.append(_LeaseWindow(contract.contract_id, contract.title, landlords, premises, start, end))

        signals = []
        for a, b in combinations(windows, 2):
            if a.contract_id == b.contract_id or a.premises != b.premises or not (a.landlords & b.landlords):
                continue
            if a.start <= b.end and b.start <= a.end:
                landlords = sorted(a.landlords & b.landlords)
                signals.append(FraudSignal(
                    rule_id="LEASE_OVERLAP", severity="HIGH",
                    entity_ids=[a.contract_id, b.contract_id, *landlords],
                    evidence=(
                        f"{a.premises} from {', '.join(snapshot.display_name(p) for p in landlords)} is leased under "
                        f"'{a.title}' ({a.start}–{a.end}) and '{b.title}' ({b.start}–{b.end}) at the same time"
                    ),
                    source_doc_ids=sorted({a.contract_id, b.contract_id}),
                ))
        return signals

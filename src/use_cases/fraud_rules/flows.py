from typing import List
import networkx as nx
from src.domain.fraud import FraudGraphSnapshot, FraudSignal
from src.interfaces.fraud_rule import IFraudRule

class CircularFlowRule(IFraudRule):
    """Money that travels A → B → C → A across invoices is round-tripping: it inflates revenue
    or launders funds without any real service changing hands. Two-party cycles are excluded
    by default because mutual billing between partners is common and legitimate."""

    def __init__(self, min_length: int = 3, max_length: int = 6):
        self.min_length = min_length
        self.max_length = max_length

    def evaluate(self, snapshot: FraudGraphSnapshot) -> List[FraudSignal]:
        flows = nx.DiGraph()
        for inv in snapshot.invoices:
            if inv.bill_to_id and inv.bill_to_id != inv.vendor_id:
                # Money moves from the billed party to the vendor
                if not flows.has_edge(inv.bill_to_id, inv.vendor_id):
                    flows.add_edge(inv.bill_to_id, inv.vendor_id, invoices=set(), docs=set())
                edge = flows.edges[inv.bill_to_id, inv.vendor_id]
                edge["invoices"].add(inv.invoice_id)
                edge["docs"].add(inv.source_doc_id)

        signals = []
        for cycle in nx.simple_cycles(flows, length_bound=self.max_length):
            if len(cycle) < self.min_length:
                continue
            hops = list(zip(cycle, cycle[1:] + cycle[:1]))
            invoices = sorted({i for u, v in hops for i in flows.edges[u, v]["invoices"]})
            path = " → ".join(snapshot.display_name(p) for p in cycle + cycle[:1])
            signals.append(FraudSignal(
                rule_id="CIRCULAR_FLOW", severity="MEDIUM", entity_ids=[*cycle, *invoices],
                evidence=f"Funds circulate {path} across {len(invoices)} invoices",
                source_doc_ids=sorted({d for u, v in hops for d in flows.edges[u, v]["docs"]}),
            ))
        return signals

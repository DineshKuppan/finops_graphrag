import networkx as nx
from typing import List, Literal, Optional
from src.interfaces.graph_storage import IGraphStorage
from src.interfaces.fraud_graph_reader import IFraudGraphReader
from src.domain import FinOpsContractGraph
from src.domain.base import Party
from src.domain.identity import canonical_party_key, canonical_identifier
from src.domain.fraud import ContractRecord, FraudGraphSnapshot, InvoiceRecord, LeaseRecord, PartyRecord

_IDENTIFIER_PREFIX = {"TaxId": "taxid", "BankAccount": "bank"}

class NetworkXGraphRepository(IGraphStorage, IFraudGraphReader):
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def save_contract_graph(self, contract_data: FinOpsContractGraph) -> None:
        c_id = contract_data.ulid
        
        # 1. Base Contract Node
        self.graph.add_node(c_id, type="Contract", title=contract_data.title, status=contract_data.status)
        
        # 2. Context Isolation
        context_id = f"ctx_{c_id}"
        self.graph.add_node(context_id, type="Context", domain=contract_data.context.domain, doc_type=contract_data.context.doc_type)
        self.graph.add_edge(c_id, context_id, relation="CATEGORIZED_AS")

        # 3. Map Parties (entity-resolved, so name variants share one node)
        for p in contract_data.parties:
            p_id = self._upsert_party(p, declared_in=c_id)
            self.graph.add_edge(c_id, p_id, relation="PARTY_TO", role=p.role)

        # 4. Map Penalties Track
        for idx, pc in enumerate(contract_data.penalty_clauses):
            pc_id = f"penalty_{c_id}_{idx}"
            self.graph.add_node(pc_id, type="PenaltyClause", clause_type=pc.clause_type, amount=pc.amount)
            self.graph.add_edge(c_id, pc_id, relation="HAS_PENALTY")
            
            if pc.breach_event:
                be_id = f"breach_{pc_id}"
                self.graph.add_node(be_id, type="BreachEvent", condition=pc.breach_event.condition)
                self.graph.add_edge(pc_id, be_id, relation="TRIGGERED_BY")

        # 5. Map Realty Lease Track
        for idx, lt in enumerate(contract_data.lease_terms):
            lt_id = f"lease_{c_id}_{idx}"
            premises = lt.rent_schedule.premises if lt.rent_schedule else None
            self.graph.add_node(
                lt_id, type="LeaseTerm", start=lt.start_date, end=lt.end_date, area=lt.area_sqft,
                floor=premises.floor if premises else None, unit=premises.unit if premises else None,
            )
            self.graph.add_edge(c_id, lt_id, relation="DEFINES_LEASE")

        # 6. Map Financial Terms Track
        for idx, ft in enumerate(contract_data.financial_terms):
            ft_id = f"fin_term_{c_id}_{idx}"
            schedule = ft.payment_schedule
            self.graph.add_node(
                ft_id, type="FinancialTerm", name=ft.name, value=ft.value, currency=ft.currency,
                frequency=schedule.frequency if schedule else None,
                payment_method=schedule.method if schedule else None,
            )
            self.graph.add_edge(c_id, ft_id, relation="HAS_FINANCIALS")

        # 7. Map Invoices Track
        for idx, inv in enumerate(contract_data.invoices):
            inv_id = f"invoice_{c_id}_{idx}"
            self.graph.add_node(
                inv_id, type="Invoice", invoice_number=inv.invoice_number, amount=inv.amount,
                currency=inv.currency, issue_date=inv.issue_date, payment_method=inv.payment_method,
                contract_ref=inv.contract_ref, source_doc=c_id,
            )
            self.graph.add_edge(c_id, inv_id, relation="CONTAINS_INVOICE")
            self.graph.add_edge(inv_id, self._upsert_party(inv.vendor, declared_in=c_id), relation="ISSUED_BY")
            if inv.bill_to:
                self.graph.add_edge(inv_id, self._upsert_party(inv.bill_to, declared_in=c_id), relation="BILLED_TO")
            if inv.contract_ref:
                # The contract may not be ingested yet; its node gets attributes once it is.
                self.graph.add_edge(inv_id, inv.contract_ref, relation="BILLED_UNDER")
            if inv.remit_to_account:
                bank_id = self._upsert_identifier("BankAccount", inv.remit_to_account)
                self.graph.add_edge(inv_id, bank_id, relation="REMIT_TO")

    def _upsert_party(self, party: Party, declared_in: str) -> str:
        p_id = f"party_{canonical_party_key(party.name)}"
        if p_id not in self.graph:
            self.graph.add_node(p_id, type="Party", name=party.name, role=party.role, aliases=set())
        self.graph.nodes[p_id]["aliases"].add(party.name)

        # declared_in records which document asserted the identifier (used for drift checks)
        if party.tax_id:
            tax_node = self._upsert_identifier("TaxId", party.tax_id)
            self.graph.add_edge(p_id, tax_node, relation="IDENTIFIED_BY", declared_in=declared_in)
        if party.bank_account:
            bank_node = self._upsert_identifier("BankAccount", party.bank_account)
            self.graph.add_edge(p_id, bank_node, relation="PAID_TO", declared_in=declared_in)
        return p_id

    def _upsert_identifier(self, kind: str, raw_value: str) -> str:
        value = canonical_identifier(raw_value)
        node_id = f"{_IDENTIFIER_PREFIX[kind]}_{value}"
        self.graph.add_node(node_id, type=kind, value=value)
        return node_id

    def fetch_subgraph_context(self, domain_filter: Literal["REALTY", "Subscription"]) -> str:
        context_strings = []
        target_contracts = []

        # Locate contracts associated with target domain context
        for node, data in self.graph.nodes(data=True):
            if data.get("type") == "Context" and data.get("domain") == domain_filter:
                for source, _, _ in self.graph.in_edges(node, data=True):
                    if self.graph.nodes[source].get("type") == "Contract":
                        target_contracts.append(source)

        # Build structural knowledge summary strings
        for c_id in target_contracts:
            c_data = self.graph.nodes[c_id]
            context_strings.append(f"Contract Object: {c_data.get('title')} (ID: {c_id})")
            
            for _, downstream, edge_data in self.graph.out_edges(c_id, data=True):
                attrs = self.graph.nodes[downstream]
                t = attrs.get("type")
                if t == "PenaltyClause":
                    context_strings.append(f"  - Penalty Found ({attrs.get('clause_type')}): Base Value = {attrs.get('amount')}")
                elif t == "LeaseTerm":
                    context_strings.append(f"  - Realty Lease Window: Area = {attrs.get('area')} sqft, Timeline = {attrs.get('start')} to {attrs.get('end')}")
                elif t == "FinancialTerm":
                    context_strings.append(f"  - Metric: {attrs.get('name')} = {attrs.get('value')}")
                elif t == "Invoice":
                    context_strings.append(f"  - Invoice {attrs.get('invoice_number')}: {attrs.get('amount')} {attrs.get('currency')}")
                    
        return "\n".join(context_strings) if context_strings else "No active sub-graph data found matching filter."

    def fetch_fraud_snapshot(self) -> FraudGraphSnapshot:
        snapshot = FraudGraphSnapshot()
        for node_id, data in self.graph.nodes(data=True):
            t = data.get("type")
            if t == "Party":
                snapshot.parties[node_id] = PartyRecord(
                    party_id=node_id, names=[data["name"], *sorted(data["aliases"] - {data["name"]})],
                    tax_ids=self._linked_values(node_id, "IDENTIFIED_BY"),
                    bank_accounts=self._linked_values(node_id, "PAID_TO"),
                )
            elif t == "Contract":
                snapshot.contracts[node_id] = self._contract_record(node_id, data)
            elif t == "Invoice":
                snapshot.invoices.append(self._invoice_record(node_id, data))
        return snapshot

    def _linked_values(self, node_id: str, relation: str, declared_in: Optional[str] = None) -> List[str]:
        return sorted({
            self.graph.nodes[target]["value"]
            for _, target, edge in self.graph.out_edges(node_id, data=True)
            if edge.get("relation") == relation and declared_in in (None, edge.get("declared_in"))
        })

    def _contract_record(self, c_id: str, data: dict) -> ContractRecord:
        record = ContractRecord(contract_id=c_id, title=data.get("title", ""), status=data.get("status", ""))
        for _, target, edge in self.graph.out_edges(c_id, data=True):
            relation, attrs = edge.get("relation"), self.graph.nodes[target]
            if relation == "PARTY_TO":
                record.party_roles[target] = edge.get("role", "")
                accounts = self._linked_values(target, "PAID_TO", declared_in=c_id)
                if accounts:
                    record.declared_accounts[target] = accounts
            elif relation == "HAS_FINANCIALS":
                record.term_values.append(attrs["value"])
                if attrs.get("payment_method"):
                    record.payment_methods.append(attrs["payment_method"])
            elif relation == "DEFINES_LEASE":
                record.leases.append(LeaseRecord(
                    start_date=attrs.get("start"), end_date=attrs.get("end"),
                    floor=attrs.get("floor"), unit=attrs.get("unit"),
                ))
        return record

    def _invoice_record(self, inv_id: str, data: dict) -> InvoiceRecord:
        links = {edge["relation"]: target for _, target, edge in self.graph.out_edges(inv_id, data=True)}
        remit_node = links.get("REMIT_TO")
        return InvoiceRecord(
            invoice_id=inv_id, invoice_number=data["invoice_number"], source_doc_id=data["source_doc"],
            vendor_id=links["ISSUED_BY"], bill_to_id=links.get("BILLED_TO"),
            amount=data["amount"], currency=data["currency"], issue_date=data.get("issue_date"),
            contract_ref=data.get("contract_ref"), payment_method=data.get("payment_method"),
            remit_to_account=self.graph.nodes[remit_node]["value"] if remit_node else None,
        )

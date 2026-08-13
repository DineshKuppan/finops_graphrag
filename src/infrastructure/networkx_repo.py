import networkx as nx
from typing import Literal
from src.interfaces.graph_storage import IGraphStorage
from src.domain import FinOpsContractGraph

class NetworkXGraphRepository(IGraphStorage):
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

        # 3. Map Parties
        for p in contract_data.parties:
            p_id = f"party_{p.name.replace(' ', '_').lower()}"
            self.graph.add_node(p_id, type="Party", name=p.name, role=p.role)
            self.graph.add_edge(c_id, p_id, relation="PARTY_TO")

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
            self.graph.add_node(lt_id, type="LeaseTerm", start=lt.start_date, end=lt.end_date, area=lt.area_sqft)
            self.graph.add_edge(c_id, lt_id, relation="DEFINES_LEASE")

        # 6. Map Financial Terms Track
        for idx, ft in enumerate(contract_data.financial_terms):
            ft_id = f"fin_term_{c_id}_{idx}"
            self.graph.add_node(ft_id, type="FinancialTerm", name=ft.name, value=ft.value)
            self.graph.add_edge(c_id, ft_id, relation="HAS_FINANCIALS")

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
                    
        return "\n".join(context_strings) if context_strings else "No active sub-graph data found matching filter."
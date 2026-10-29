from src.domain.base import Party
from src.domain.invoices import Invoice
from tests.factories import BUYER, contract, invoice_doc, lease, repo_with, term


def _relations(repo, node_id):
    return {(edge["relation"], target) for _, target, edge in repo.graph.out_edges(node_id, data=True)}


def test_party_name_variants_merge_into_one_node():
    repo = repo_with(
        contract("c1", [Party(name="ACME, Inc.", role="Vendor"), BUYER]),
        contract("c2", [Party(name="Acme Inc", role="Vendor"), BUYER]),
    )
    parties = [n for n, d in repo.graph.nodes(data=True) if d["type"] == "Party"]
    assert sorted(parties) == ["party_acme", "party_finops"]
    assert repo.graph.nodes["party_acme"]["aliases"] == {"ACME, Inc.", "Acme Inc"}


def test_role_is_kept_per_contract_on_the_edge():
    repo = repo_with(contract("c1", [Party(name="Acme", role="Vendor")]))
    roles = [e["role"] for _, _, e in repo.graph.out_edges("c1", data=True) if e["relation"] == "PARTY_TO"]
    assert roles == ["Vendor"]


def test_identifiers_become_shared_nodes_with_provenance():
    repo = repo_with(contract("c1", [Party(name="Acme", role="Vendor", tax_id="12-3456789", bank_account="GB29 NWBK 6016")]))
    assert ("IDENTIFIED_BY", "taxid_123456789") in _relations(repo, "party_acme")
    assert ("PAID_TO", "bank_GB29NWBK6016") in _relations(repo, "party_acme")
    paid_to = [e for _, t, e in repo.graph.out_edges("party_acme", data=True) if e["relation"] == "PAID_TO"]
    assert paid_to[0]["declared_in"] == "c1"


def test_invoice_is_linked_to_vendor_payer_contract_and_account():
    inv = Invoice(
        invoice_number="INV-1", vendor=Party(name="Acme", role="Vendor"), bill_to=BUYER,
        amount=500, contract_ref="c1", remit_to_account="999-111",
    )
    repo = repo_with(invoice_doc("batch1", [inv]))
    assert _relations(repo, "invoice_batch1_0") == {
        ("ISSUED_BY", "party_acme"), ("BILLED_TO", "party_finops"),
        ("BILLED_UNDER", "c1"), ("REMIT_TO", "bank_999111"),
    }
    assert ("CONTAINS_INVOICE", "invoice_batch1_0") in _relations(repo, "batch1")


def test_invoice_ingested_before_its_contract_still_links():
    inv = Invoice(invoice_number="INV-1", vendor=Party(name="Acme", role="Vendor"), amount=1, contract_ref="c1")
    repo = repo_with(invoice_doc("batch1", [inv]), contract("c1", [Party(name="Acme", role="Vendor")]))
    assert repo.graph.nodes["c1"]["type"] == "Contract"
    assert ("BILLED_UNDER", "c1") in _relations(repo, "invoice_batch1_0")


def test_term_and_lease_carry_fraud_relevant_attributes():
    repo = repo_with(contract("c1", [BUYER], terms=[term(100, method="Wire")], leases=[lease("2026-01-01", "2026-12-31")]))
    assert repo.graph.nodes["fin_term_c1_0"]["payment_method"] == "Wire"
    assert repo.graph.nodes["lease_c1_0"]["unit"] == "301"


def test_rag_context_includes_invoices():
    inv = Invoice(invoice_number="INV-9", vendor=Party(name="Acme", role="Vendor"), amount=42)
    repo = repo_with(invoice_doc("batch1", [inv]))
    assert "Invoice INV-9: 42.0 USD" in repo.fetch_subgraph_context("Subscription")

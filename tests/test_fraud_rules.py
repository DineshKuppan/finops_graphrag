from src.domain.base import Party
from src.domain.invoices import Invoice
from src.use_cases.fraud_rules.billing import ContractOverbillingRule, DuplicateBillingRule
from src.use_cases.fraud_rules.identifiers import SharedIdentifierRule
from tests.factories import BUYER, contract, invoice_doc, repo_with, term


def _run(rule, *docs):
    return rule.evaluate(repo_with(*docs).fetch_fraud_snapshot())


def _inv(number, amount, vendor="Acme", date=None, **kwargs):
    return Invoice(invoice_number=number, vendor=Party(name=vendor, role="Vendor"), amount=amount, issue_date=date, **kwargs)


# --- SharedIdentifierRule ---

def test_two_vendors_declaring_one_bank_account_is_flagged_and_masked():
    signals = _run(
        SharedIdentifierRule(),
        contract("c1", [Party(name="Acme", role="Vendor", bank_account="GB29-0000-9876"), BUYER]),
        contract("c2", [Party(name="Apex Supplies", role="Vendor", bank_account="gb2900009876"), BUYER]),
    )
    (signal,) = signals
    assert (signal.rule_id, signal.severity) == ("SHARED_BANK_ACCOUNT", "HIGH")
    assert signal.entity_ids == ["party_acme", "party_apex_supplies"]
    assert signal.source_doc_ids == ["c1", "c2"]
    assert "****9876" in signal.evidence and "GB29" not in signal.evidence


def test_invoice_remitting_to_another_vendors_account_is_flagged():
    signals = _run(
        SharedIdentifierRule(),
        contract("c1", [Party(name="Acme", role="Vendor", bank_account="ACC-1"), BUYER]),
        invoice_doc("b1", [_inv("X-1", 10, vendor="Shadow LLC", remit_to_account="ACC-1")]),
    )
    assert [s.entity_ids for s in signals] == [["party_acme", "party_shadow"]]


def test_shared_tax_id_is_flagged():
    signals = _run(
        SharedIdentifierRule(),
        contract("c1", [Party(name="Acme", role="Vendor", tax_id="12-3456789")]),
        contract("c2", [Party(name="Beta Corp", role="Vendor", tax_id="123456789")]),
    )
    assert [s.rule_id for s in signals] == ["SHARED_TAX_ID"]


def test_name_variants_of_one_vendor_are_not_flagged():
    signals = _run(
        SharedIdentifierRule(),
        contract("c1", [Party(name="ACME, Inc.", role="Vendor", bank_account="ACC-1")]),
        contract("c2", [Party(name="Acme Inc", role="Vendor", bank_account="ACC-1")]),
    )
    assert signals == []


# --- DuplicateBillingRule ---

def test_repeated_invoice_number_is_high():
    signals = _run(DuplicateBillingRule(), invoice_doc("b1", [_inv("INV-7", 100)]), invoice_doc("b2", [_inv("inv-7 ", 250)]))
    (signal,) = signals
    assert (signal.rule_id, signal.severity, signal.source_doc_ids) == ("DUPLICATE_INVOICE_NUMBER", "HIGH", ["b1", "b2"])


def test_same_amount_within_window_is_medium():
    signals = _run(DuplicateBillingRule(), invoice_doc("b1", [_inv("A", 990, date="2026-03-01"), _inv("B", 990, date="2026-03-09")]))
    assert [(s.rule_id, s.severity) for s in signals] == [("DUPLICATE_AMOUNT", "MEDIUM")]


def test_monthly_recurring_charge_is_not_a_duplicate():
    signals = _run(DuplicateBillingRule(), invoice_doc("b1", [_inv("A", 990, date="2026-02-01"), _inv("B", 990, date="2026-03-01")]))
    assert signals == []


def test_same_amount_from_different_vendors_or_without_dates_is_ignored():
    signals = _run(DuplicateBillingRule(), invoice_doc("b1", [
        _inv("A", 990, vendor="Acme", date="2026-03-01"), _inv("B", 990, vendor="Beta", date="2026-03-02"),
        _inv("C", 50), _inv("D", 50),
    ]))
    assert signals == []


# --- ContractOverbillingRule ---

def test_invoice_above_largest_term_is_flagged():
    signals = _run(
        ContractOverbillingRule(),
        contract("c1", [Party(name="Acme", role="Vendor")], terms=[term(1000), term(400)]),
        invoice_doc("b1", [_inv("A", 1500, contract_ref="c1"), _inv("B", 2500, contract_ref="c1"), _inv("C", 1000, contract_ref="c1")]),
    )
    assert [(s.entity_ids[0], s.severity) for s in signals] == [("invoice_b1_0", "MEDIUM"), ("invoice_b1_1", "HIGH")]


def test_overbilling_respects_tolerance_and_skips_unpriced_contracts():
    docs = (
        contract("c1", [Party(name="Acme", role="Vendor")], terms=[term(1000)]),
        contract("c2", [Party(name="Acme", role="Vendor")]),
        invoice_doc("b1", [_inv("A", 1050, contract_ref="c1"), _inv("B", 9999, contract_ref="c2")]),
    )
    assert _run(ContractOverbillingRule(tolerance=0.1), *docs) == []

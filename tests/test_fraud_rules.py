from src.domain.base import Party
from src.domain.invoices import Invoice
from src.use_cases.fraud_rules import default_rules
from src.use_cases.fraud_rules.billing import (
    ContractOverbillingRule, DuplicateBillingRule, OrphanInvoiceRule, PaymentDriftRule,
)
from src.use_cases.fraud_rules.flows import CircularFlowRule
from src.use_cases.fraud_rules.identifiers import SharedIdentifierRule
from src.use_cases.fraud_rules.realty import LeaseOverlapRule
from tests.factories import BUYER, contract, invoice_doc, lease, repo_with, term


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


# --- OrphanInvoiceRule ---

def test_orphan_invoice_cases():
    acme = Party(name="Acme", role="Vendor")
    signals = _run(
        OrphanInvoiceRule(),
        contract("live", [acme, BUYER]),
        contract("dead", [acme, BUYER], status="Terminated"),
        contract("other", [Party(name="Beta", role="Vendor"), BUYER]),
        invoice_doc("b1", [
            _inv("ok", 1, contract_ref="live"),
            _inv("no-ref", 1),
            _inv("ghost", 1, contract_ref="missing"),
            _inv("expired", 1, contract_ref="dead"),
            _inv("stranger", 1, contract_ref="other"),
        ]),
    )
    found = {s.evidence.split()[1]: s.severity for s in signals}
    assert found == {"no-ref": "MEDIUM", "ghost": "HIGH", "expired": "HIGH", "stranger": "HIGH"}


def test_unrecognised_status_is_treated_as_active():
    signals = _run(
        OrphanInvoiceRule(),
        contract("c1", [Party(name="Acme", role="Vendor")], status="Pending Renewal"),
        invoice_doc("b1", [_inv("A", 1, contract_ref="c1")]),
    )
    assert signals == []


# --- PaymentDriftRule ---

def test_remittance_account_change_is_high_and_method_change_is_medium():
    signals = _run(
        PaymentDriftRule(),
        contract("c1", [Party(name="Acme", role="Vendor", bank_account="OLD-1111"), BUYER], terms=[term(100, method="ACH")]),
        invoice_doc("b1", [_inv("A", 50, contract_ref="c1", payment_method="Wire", remit_to_account="NEW-2222")]),
    )
    assert {(s.rule_id, s.severity) for s in signals} == {("PAYMENT_METHOD_DRIFT", "MEDIUM"), ("REMITTANCE_ACCOUNT_DRIFT", "HIGH")}
    drift = next(s for s in signals if s.rule_id == "REMITTANCE_ACCOUNT_DRIFT")
    assert "****2222" in drift.evidence and "****1111" in drift.evidence and "NEW" not in drift.evidence


def test_matching_payment_details_and_accounts_declared_elsewhere_do_not_drift():
    signals = _run(
        PaymentDriftRule(),
        contract("c1", [Party(name="Acme", role="Vendor", bank_account="ACC-1"), BUYER], terms=[term(100, method="ACH")]),
        # The invoice document re-declares the vendor's account; only the contract's declaration is trusted
        invoice_doc("b1", [Invoice(
            invoice_number="A", vendor=Party(name="Acme", role="Vendor", bank_account="ACC-9"), amount=1,
            contract_ref="c1", payment_method="ach", remit_to_account="acc 1",
        )]),
    )
    assert signals == []


# --- LeaseOverlapRule ---

LANDLORD = Party(name="Skyline Properties", role="Landlord")


def test_same_unit_leased_twice_by_same_landlord_is_flagged():
    signals = _run(
        LeaseOverlapRule(),
        contract("l1", [LANDLORD, BUYER], leases=[lease("2026-01-01", "2026-12-31")], doc_type="Office Lease", domain="REALTY"),
        contract("l2", [LANDLORD, BUYER], leases=[lease("2026-06-01", "2027-05-31", floor="3 ", unit="3-01")], doc_type="Office Lease", domain="REALTY"),
    )
    (signal,) = signals
    assert signal.entity_ids == ["l1", "l2", "party_skyline_properties"]


def test_non_overlapping_or_different_landlord_leases_are_ignored():
    other_landlord = Party(name="Harbor Realty", role="Lessor")
    signals = _run(
        LeaseOverlapRule(),
        contract("l1", [LANDLORD, BUYER], leases=[lease("2026-01-01", "2026-12-31")]),
        contract("l2", [LANDLORD, BUYER], leases=[lease("2027-01-01", "2027-12-31")]),
        contract("l3", [other_landlord, BUYER], leases=[lease("2026-01-01", "2026-12-31")]),
        # Shares only the tenant with l1: the same unit number in another building is not a conflict
        contract("l4", [BUYER], leases=[lease("2026-01-01", "2026-12-31")]),
    )
    assert signals == []


# --- CircularFlowRule ---

def _billed(number, vendor, payer):
    return Invoice(invoice_number=number, vendor=Party(name=vendor, role="Vendor"), bill_to=Party(name=payer, role="Customer"), amount=10_000)


def test_three_party_round_trip_is_flagged():
    signals = _run(CircularFlowRule(), invoice_doc("b1", [_billed("1", "B", "A"), _billed("2", "C", "B"), _billed("3", "A", "C")]))
    (signal,) = signals
    assert signal.rule_id == "CIRCULAR_FLOW"
    assert set(signal.entity_ids) == {"party_a", "party_b", "party_c", "invoice_b1_0", "invoice_b1_1", "invoice_b1_2"}


def test_mutual_billing_and_open_chains_are_ignored():
    signals = _run(CircularFlowRule(), invoice_doc("b1", [_billed("1", "B", "A"), _billed("2", "A", "B"), _billed("3", "C", "B")]))
    assert signals == []


def test_default_rules_cover_every_signal_family():
    assert {type(r).__name__ for r in default_rules()} == {
        "SharedIdentifierRule", "DuplicateBillingRule", "ContractOverbillingRule", "OrphanInvoiceRule",
        "PaymentDriftRule", "LeaseOverlapRule", "CircularFlowRule",
    }

import pytest
from src.domain.base import Party
from src.domain.invoices import Invoice
from src.infrastructure.isolation_forest_detector import IsolationForestAnomalyDetector
from src.interfaces.anomaly_detector import IAnomalyDetector
from src.use_cases.fraud_rules import default_rules
from src.use_cases.fraud_rules.anomaly import VendorAnomalyRule, robust_deviations, vendor_features
from tests.factories import BUYER, contract, invoice_doc, repo_with, term


class FixedDetector(IAnomalyDetector):
    def __init__(self, value):
        self.value, self.calls = value, 0

    def score(self, rows):
        self.calls += 1
        return [self.value] * len(rows)


def _population(vendors=20, rogue=True):
    """Ordinary vendors bill a contracted amount roughly monthly; the rogue vendor bills
    round sums every few days, with no contract, into a rotating set of accounts."""
    docs = []
    for i in range(vendors):
        name, cid = f"Vendor {i:02d}", f"c{i}"
        docs.append(contract(cid, [Party(name=name, role="Vendor"), BUYER], terms=[term(5000)]))
        docs.append(invoice_doc(f"b{i}", [
            Invoice(invoice_number=f"V{i}-{m}", vendor=Party(name=name, role="Vendor"), bill_to=BUYER,
                    amount=4000 + 37 * i + 11 * m, issue_date=f"2026-0{m}-0{1 + i % 9}",
                    contract_ref=cid, remit_to_account=f"ACC-{i:04d}")
            for m in (1, 2, 3)
        ]))
    if rogue:
        docs.append(invoice_doc("rogue", [
            Invoice(invoice_number=f"R-{n}", vendor=Party(name="Swift Consulting", role="Vendor"), bill_to=BUYER,
                    amount=9000, issue_date=f"2026-03-{1 + 2 * n:02d}", remit_to_account=f"ROT-{n % 4}")
            for n in range(12)
        ]))
    return repo_with(*docs).fetch_fraud_snapshot()


def test_features_describe_vendor_behaviour():
    rows = vendor_features(_population(vendors=1))
    rogue, regular = rows["party_swift_consulting"], rows["party_vendor_00"]
    assert rogue["invoice_count"] == 12
    assert rogue["distinct_remit_accounts"] == 4
    assert rogue["uncontracted_share"] == 1.0 and regular["uncontracted_share"] == 0.0
    assert rogue["round_amount_share"] == 1.0
    assert rogue["invoices_per_30_days"] == pytest.approx(12 * 30 / 30)
    assert regular["invoices_per_30_days"] == pytest.approx(3 * 30 / 59)
    assert rogue["amount_variation"] == 0.0


def test_robust_deviation_handles_identical_peers():
    assert robust_deviations([1, 1, 1, 1, 4])[-1] > 3
    assert robust_deviations([2, 2, 2]) == [0.0, 0.0, 0.0]


def test_isolation_forest_flags_only_the_rogue_vendor_with_reasons():
    signals = VendorAnomalyRule(IsolationForestAnomalyDetector()).evaluate(_population())
    (signal,) = signals
    assert (signal.rule_id, signal.entity_ids, signal.severity) == ("VENDOR_ANOMALY", ["party_swift_consulting"], "MEDIUM")
    assert "behaves unlike its 20 peers" in signal.evidence
    assert "invoices issued 12 vs peer median 3" in signal.evidence
    assert "share of round-thousand amounts 100% vs peer median 0%" in signal.evidence
    assert signal.source_doc_ids == ["rogue"]


def test_ordinary_population_is_not_flagged():
    assert VendorAnomalyRule(IsolationForestAnomalyDetector()).evaluate(_population(rogue=False)) == []


def test_small_population_is_skipped_without_scoring():
    detector = FixedDetector(0.99)
    assert VendorAnomalyRule(detector, min_vendors=8).evaluate(_population(vendors=3)) == []
    assert detector.calls == 0


def test_high_score_without_an_explainable_deviation_is_not_flagged():
    assert VendorAnomalyRule(FixedDetector(0.99)).evaluate(_population(rogue=False)) == []


def test_low_score_is_not_flagged_even_with_deviations():
    assert VendorAnomalyRule(FixedDetector(0.5)).evaluate(_population()) == []


def test_default_rules_enable_anomaly_detection_only_with_a_detector():
    assert not any(isinstance(r, VendorAnomalyRule) for r in default_rules())
    assert any(isinstance(r, VendorAnomalyRule) for r in default_rules(FixedDetector(0)))

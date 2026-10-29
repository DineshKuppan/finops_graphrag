import pytest
from src.domain.fraud import FraudGraphSnapshot, FraudSignal, InvoiceRecord, PartyRecord
from src.interfaces.fraud_graph_reader import IFraudGraphReader
from src.interfaces.fraud_rule import IFraudRule
from src.use_cases.detect_fraud import DetectFraudSignalsUseCase


class StubReader(IFraudGraphReader):
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def fetch_fraud_snapshot(self):
        return self.snapshot


class StubRule(IFraudRule):
    def __init__(self, *signals):
        self.signals = list(signals)

    def evaluate(self, snapshot):
        return self.signals


SNAPSHOT = FraudGraphSnapshot(
    parties={"party_a": PartyRecord(party_id="party_a", names=["A"])},
    invoices=[InvoiceRecord(invoice_id="inv_1", invoice_number="1", source_doc_id="d", vendor_id="party_a", amount=1, currency="USD")],
)


def _signal(severity, *entities, rule_id="R"):
    return FraudSignal(rule_id=rule_id, severity=severity, entity_ids=list(entities), evidence="e", source_doc_ids=["doc1"])


def test_scores_combine_as_noisy_or_and_rank_descending():
    assessment = DetectFraudSignalsUseCase(
        StubReader(SNAPSHOT),
        [StubRule(_signal("HIGH", "party_a", "inv_1")), StubRule(_signal("MEDIUM", "party_a"), _signal("LOW", "c_x"))],
    ).execute()

    scores = {r.entity_id: (r.entity_type, r.score) for r in assessment.reports}
    assert scores["party_a"] == ("Party", pytest.approx(1 - 0.2 * 0.5))
    assert scores["inv_1"] == ("Invoice", 0.8)
    assert scores["c_x"] == ("Unknown", 0.2)
    assert [r.entity_id for r in assessment.reports] == ["party_a", "inv_1", "c_x"]
    assert [s.severity for s in assessment.signals] == ["HIGH", "MEDIUM", "LOW"]


def test_entity_repeated_within_one_signal_counts_once():
    (report,) = DetectFraudSignalsUseCase(StubReader(SNAPSHOT), [StubRule(_signal("HIGH", "party_a", "party_a"))]).execute().reports
    assert report.score == 0.8


def test_prompt_carries_evidence_ranking_and_guardrails():
    prompt = DetectFraudSignalsUseCase(StubReader(SNAPSHOT), [StubRule(_signal("HIGH", "party_a", rule_id="SHARED_TAX_ID"))]).execute().explanation_prompt
    assert "[HIGH] SHARED_TAX_ID: e (entities: party_a; sources: doc1)" in prompt
    assert "party_a (Party): risk 0.80" in prompt
    assert "do not label anything as confirmed fraud" in prompt


def test_clean_graph_reports_nothing():
    assessment = DetectFraudSignalsUseCase(StubReader(SNAPSHOT), [StubRule()]).execute()
    assert (assessment.signals, assessment.reports) == ([], [])
    assert "No fraud signals detected." in assessment.explanation_prompt

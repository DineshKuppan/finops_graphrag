from datetime import datetime

import pytest
from src.domain.fraud import FraudGraphSnapshot, FraudSignal, PartyRecord, ReviewFeedback
from src.infrastructure.jsonl_feedback_store import JsonlFeedbackStore
from src.use_cases.detect_fraud import DetectFraudSignalsUseCase
from src.use_cases.review_feedback import RecordReviewFeedbackUseCase, RuleCalibration, calibrate
from tests.test_detect_fraud import StubReader, StubRule

SIGNAL = FraudSignal(rule_id="DUPLICATE_AMOUNT", severity="MEDIUM", entity_ids=["party_a"], evidence="e")
SNAPSHOT = FraudGraphSnapshot(parties={"party_a": PartyRecord(party_id="party_a", names=["A"])})


def _verdict(rule_id, verdict):
    return ReviewFeedback(rule_id=rule_id, verdict=verdict, recorded_at="2026-10-29T00:00:00+00:00")


def test_calibration_tallies_verdicts_per_rule():
    tallies = calibrate([_verdict("A", "CONFIRMED"), _verdict("A", "DISMISSED"), _verdict("A", "DISMISSED"), _verdict("B", "CONFIRMED")])
    assert tallies == {"A": RuleCalibration(confirmed=1, dismissed=2), "B": RuleCalibration(confirmed=1, dismissed=0)}


def test_weight_starts_at_prior_and_converges_to_observed_precision():
    assert RuleCalibration().weight(prior=0.5, prior_strength=5) == 0.5
    assert RuleCalibration(confirmed=1, dismissed=9).weight(0.5, 5) == pytest.approx((2.5 + 1) / 15)
    assert RuleCalibration(confirmed=0, dismissed=1000).weight(0.8, 5) < 0.01
    assert RuleCalibration(confirmed=1000, dismissed=0).weight(0.2, 5) > 0.99


def test_jsonl_store_round_trips_and_appends(tmp_path):
    store = JsonlFeedbackStore(tmp_path / "nested" / "feedback.jsonl")
    assert store.list_feedback() == []
    store.record(_verdict("A", "CONFIRMED"))
    store.record(_verdict("B", "DISMISSED"))
    assert [(f.rule_id, f.verdict) for f in JsonlFeedbackStore(store.path).list_feedback()] == [("A", "CONFIRMED"), ("B", "DISMISSED")]


def test_recording_a_verdict_captures_the_signal(tmp_path):
    store = JsonlFeedbackStore(tmp_path / "feedback.jsonl")
    feedback = RecordReviewFeedbackUseCase(store).execute(SIGNAL, "DISMISSED", reviewer="ap-analyst", note="recurring retainer")
    assert (feedback.rule_id, feedback.entity_ids, feedback.reviewer) == ("DUPLICATE_AMOUNT", ["party_a"], "ap-analyst")
    assert datetime.fromisoformat(feedback.recorded_at).tzinfo is not None
    assert store.list_feedback() == [feedback]


def test_dismissals_lower_risk_and_are_surfaced_in_the_prompt(tmp_path):
    store = JsonlFeedbackStore(tmp_path / "feedback.jsonl")
    detect = DetectFraudSignalsUseCase(StubReader(SNAPSHOT), [StubRule(SIGNAL)], feedback=store)
    assert detect.execute().reports[0].score == 0.5

    for _ in range(5):
        RecordReviewFeedbackUseCase(store).execute(SIGNAL, "DISMISSED")
    assessment = detect.execute()
    assert assessment.reports[0].score == pytest.approx(0.25)
    assert "[review history: 0 confirmed, 5 dismissed; weight 0.25]" in assessment.explanation_prompt


def test_feedback_for_other_rules_does_not_change_the_weight(tmp_path):
    store = JsonlFeedbackStore(tmp_path / "feedback.jsonl")
    store.record(_verdict("SHARED_TAX_ID", "DISMISSED"))
    assessment = DetectFraudSignalsUseCase(StubReader(SNAPSHOT), [StubRule(SIGNAL)], feedback=store).execute()
    assert assessment.reports[0].score == 0.5
    assert "review history" not in assessment.explanation_prompt

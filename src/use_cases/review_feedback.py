from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, Literal, Optional
from src.domain.fraud import FraudSignal, ReviewFeedback
from src.interfaces.feedback_store import IFeedbackStore

@dataclass
class RuleCalibration:
    confirmed: int = 0
    dismissed: int = 0

    def weight(self, prior: float, prior_strength: float) -> float:
        """Beta-posterior mean of the rule's precision: the severity weight acts as a prior worth
        `prior_strength` reviews, and each verdict pulls the weight toward observed reality."""
        return (prior_strength * prior + self.confirmed) / (prior_strength + self.confirmed + self.dismissed)

def calibrate(feedback: Iterable[ReviewFeedback]) -> Dict[str, RuleCalibration]:
    calibrations: Dict[str, RuleCalibration] = {}
    for item in feedback:
        tally = calibrations.setdefault(item.rule_id, RuleCalibration())
        if item.verdict == "CONFIRMED":
            tally.confirmed += 1
        else:
            tally.dismissed += 1
    return calibrations

class RecordReviewFeedbackUseCase:
    def __init__(self, store: IFeedbackStore):
        self.store = store

    def execute(
        self,
        signal: FraudSignal,
        verdict: Literal["CONFIRMED", "DISMISSED"],
        reviewer: Optional[str] = None,
        note: Optional[str] = None,
    ) -> ReviewFeedback:
        feedback = ReviewFeedback(
            rule_id=signal.rule_id, verdict=verdict, entity_ids=signal.entity_ids,
            reviewer=reviewer, note=note,
            recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        self.store.record(feedback)
        return feedback

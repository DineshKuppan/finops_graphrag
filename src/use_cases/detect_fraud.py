from collections import defaultdict
from typing import Dict, List, Optional, Sequence
from src.domain.fraud import FraudAssessment, FraudGraphSnapshot, FraudSignal, RiskReport
from src.interfaces.feedback_store import IFeedbackStore
from src.interfaces.fraud_graph_reader import IFraudGraphReader
from src.interfaces.fraud_rule import IFraudRule
from src.use_cases.review_feedback import RuleCalibration, calibrate

SEVERITY_WEIGHTS = {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8}
_SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

class DetectFraudSignalsUseCase:
    def __init__(
        self,
        reader: IFraudGraphReader,
        rules: Sequence[IFraudRule],
        feedback: Optional[IFeedbackStore] = None,
        prior_strength: float = 5.0,
    ):
        # Concrete rules are chosen at the composition root, keeping this use case closed for modification
        self.reader = reader
        self.rules = list(rules)
        self.feedback = feedback
        self.prior_strength = prior_strength

    def execute(self) -> FraudAssessment:
        snapshot = self.reader.fetch_fraud_snapshot()

        # Step 1: Deterministic detection — every signal is traceable to graph entities
        signals = [signal for rule in self.rules for signal in rule.evaluate(snapshot)]
        signals.sort(key=lambda s: _SEVERITY_ORDER[s.severity])

        # Step 2: Aggregate signals into per-entity risk, tuned by reviewer verdicts when available
        calibrations = calibrate(self.feedback.list_feedback()) if self.feedback else {}
        reports = self._rank(signals, snapshot, calibrations)

        # Step 3: Hand the evidence to the LLM to explain, never to decide
        prompt = self._build_prompt(signals, reports, calibrations)
        return FraudAssessment(signals=signals, reports=reports, explanation_prompt=prompt)

    def _weight(self, signal: FraudSignal, calibrations: Dict[str, RuleCalibration]) -> float:
        prior = SEVERITY_WEIGHTS[signal.severity]
        calibration = calibrations.get(signal.rule_id)
        return calibration.weight(prior, self.prior_strength) if calibration else prior

    def _rank(
        self, signals: List[FraudSignal], snapshot: FraudGraphSnapshot, calibrations: Dict[str, RuleCalibration],
    ) -> List[RiskReport]:
        by_entity: Dict[str, List[FraudSignal]] = defaultdict(list)
        for signal in signals:
            for entity_id in dict.fromkeys(signal.entity_ids):
                by_entity[entity_id].append(signal)

        invoice_ids = {inv.invoice_id for inv in snapshot.invoices}
        reports = []
        for entity_id, entity_signals in by_entity.items():
            # Noisy-OR: each signal is independent evidence; the score stays within [0, 1]
            clean = 1.0
            for signal in entity_signals:
                clean *= 1 - self._weight(signal, calibrations)
            if entity_id in snapshot.parties:
                entity_type = "Party"
            elif entity_id in snapshot.contracts:
                entity_type = "Contract"
            elif entity_id in invoice_ids:
                entity_type = "Invoice"
            else:
                entity_type = "Unknown"
            reports.append(RiskReport(entity_id=entity_id, entity_type=entity_type, score=round(1 - clean, 4), signals=entity_signals))
        return sorted(reports, key=lambda r: (-r.score, r.entity_id))

    def _build_prompt(
        self, signals: List[FraudSignal], reports: List[RiskReport], calibrations: Dict[str, RuleCalibration],
    ) -> str:
        if not signals:
            return "### FRAUD SIGNALS DETECTED IN GRAPH ###\nNo fraud signals detected."

        signal_lines = []
        for s in signals:
            line = (
                f"- [{s.severity}] {s.rule_id}: {s.evidence} (entities: {', '.join(s.entity_ids)}; "
                f"sources: {', '.join(s.source_doc_ids) or 'n/a'})"
            )
            if s.rule_id in calibrations:
                tally = calibrations[s.rule_id]
                line += (
                    f" [review history: {tally.confirmed} confirmed, {tally.dismissed} dismissed; "
                    f"weight {self._weight(s, calibrations):.2f}]"
                )
            signal_lines.append(line)
        ranking_lines = [f"- {r.entity_id} ({r.entity_type}): risk {r.score:.2f}" for r in reports]
        return (
            f"### FRAUD SIGNALS DETECTED IN GRAPH ###\n"
            f"{chr(10).join(signal_lines)}\n\n"
            f"### ENTITY RISK RANKING ###\n"
            f"{chr(10).join(ranking_lines)}\n\n"
            f"Instruction: Using only the signals above, explain for each high-risk entity why the pattern is "
            f"suspicious, what legitimate explanation could exist, and what a reviewer should verify next. "
            f"Do not introduce facts not listed above and do not label anything as confirmed fraud."
        )

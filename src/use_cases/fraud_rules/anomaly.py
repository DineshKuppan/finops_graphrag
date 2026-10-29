import math
from collections import defaultdict
from statistics import mean, median, pstdev
from typing import Dict, List, Sequence, Tuple
from src.domain.fraud import FraudGraphSnapshot, FraudSignal, InvoiceRecord
from src.interfaces.anomaly_detector import IAnomalyDetector
from src.interfaces.fraud_rule import IFraudRule
from src.use_cases.fraud_rules._util import parse_iso_date

# Every feature is human-readable so a flag can always be explained in reviewer terms.
# Amount-based features are log-scaled so one large vendor doesn't dominate the forest.
FEATURES: Dict[str, str] = {
    "invoice_count": "invoices issued",
    "log_total_billed": "total billed",
    "log_mean_amount": "mean invoice amount",
    "amount_variation": "invoice amount variation (CV)",
    "round_amount_share": "share of round-thousand amounts",
    "invoices_per_30_days": "invoices per 30 days",
    "distinct_remit_accounts": "distinct remittance accounts",
    "distinct_payers": "distinct payers billed",
    "uncontracted_share": "share of invoices without a known contract",
    "name_variants": "name variants",
}

def _display(feature: str, value: float) -> str:
    """Renders a feature in reviewer units: log amounts back to currency, shares as percentages."""
    if feature.startswith("log_"):
        return f"{math.expm1(value):,.0f}"
    if feature.endswith("_share"):
        return f"{value:.0%}"
    return f"{value:,.2f}".rstrip("0").rstrip(".")

def vendor_features(snapshot: FraudGraphSnapshot) -> Dict[str, Dict[str, float]]:
    """One feature row per vendor that issued at least one invoice."""
    by_vendor: Dict[str, List[InvoiceRecord]] = defaultdict(list)
    for inv in snapshot.invoices:
        by_vendor[inv.vendor_id].append(inv)

    rows = {}
    for vendor_id, invoices in by_vendor.items():
        amounts = [inv.amount for inv in invoices]
        dates = sorted(d for d in (parse_iso_date(inv.issue_date) for inv in invoices) if d)
        span_days = (dates[-1] - dates[0]).days if len(dates) > 1 else 0
        avg = mean(amounts)
        rows[vendor_id] = {
            "invoice_count": float(len(invoices)),
            "log_total_billed": math.log1p(max(sum(amounts), 0.0)),
            "log_mean_amount": math.log1p(max(avg, 0.0)),
            "amount_variation": pstdev(amounts) / avg if avg > 0 else 0.0,
            "round_amount_share": sum(a >= 1000 and a % 1000 == 0 for a in amounts) / len(amounts),
            "invoices_per_30_days": len(invoices) * 30 / max(span_days, 30),
            "distinct_remit_accounts": float(len({inv.remit_to_account for inv in invoices if inv.remit_to_account})),
            "distinct_payers": float(len({inv.bill_to_id for inv in invoices if inv.bill_to_id})),
            "uncontracted_share": sum(inv.contract_ref not in snapshot.contracts for inv in invoices) / len(invoices),
            "name_variants": float(len(snapshot.parties[vendor_id].names)) if vendor_id in snapshot.parties else 1.0,
        }
    return rows

def robust_deviations(column: Sequence[float]) -> List[float]:
    """Distance of each value from the peer median in robust standard deviations (MAD-based).
    Falls back to mean absolute deviation when most peers are identical (MAD = 0)."""
    centre = median(column)
    abs_dev = [abs(v - centre) for v in column]
    mad = median(abs_dev)
    scale = 1.4826 * mad if mad > 0 else 1.2533 * mean(abs_dev)
    return [d / scale if d > 0 and scale > 0 else 0.0 for d in abs_dev]

class VendorAnomalyRule(IFraudRule):
    """Catches unusual vendors no hand-written rule anticipates: an isolation forest scores how
    easily each vendor's behaviour separates from its peers. A vendor is flagged only when the
    forest score clears the threshold *and* at least one feature deviates strongly from the peer
    median, so every flag ships with a concrete, reviewable reason."""

    def __init__(
        self,
        detector: IAnomalyDetector,
        min_vendors: int = 8,
        score_threshold: float = 0.65,
        min_deviation: float = 3.0,
        top_features: int = 3,
    ):
        self.detector = detector
        self.min_vendors = min_vendors
        self.score_threshold = score_threshold
        self.min_deviation = min_deviation
        self.top_features = top_features

    def evaluate(self, snapshot: FraudGraphSnapshot) -> List[FraudSignal]:
        rows = vendor_features(snapshot)
        # Below a minimum population "unusual" is meaningless, so stay silent rather than guess
        if len(rows) < self.min_vendors:
            return []

        vendor_ids = sorted(rows)
        names = list(FEATURES)
        matrix = [[rows[v][f] for f in names] for v in vendor_ids]
        scores = self.detector.score(matrix)
        deviations = {f: robust_deviations([row[i] for row in matrix]) for i, f in enumerate(names)}
        peer_medians = {f: median(row[i] for row in matrix) for i, f in enumerate(names)}

        signals = []
        for idx, (vendor_id, score) in enumerate(zip(vendor_ids, scores)):
            drivers: List[Tuple[str, float]] = sorted(
                ((f, deviations[f][idx]) for f in names if deviations[f][idx] >= self.min_deviation),
                key=lambda item: -item[1],
            )[: self.top_features]
            if score < self.score_threshold or not drivers:
                continue
            reasons = "; ".join(
                f"{FEATURES[f]} {_display(f, rows[vendor_id][f])} vs peer median {_display(f, peer_medians[f])}"
                for f, _ in drivers
            )
            signals.append(FraudSignal(
                rule_id="VENDOR_ANOMALY", severity="MEDIUM" if score >= 0.75 else "LOW",
                entity_ids=[vendor_id],
                evidence=(
                    f"{snapshot.display_name(vendor_id)} behaves unlike its {len(vendor_ids) - 1} peers "
                    f"(anomaly score {score:.2f}): {reasons}"
                ),
                source_doc_ids=sorted({inv.source_doc_id for inv in snapshot.invoices if inv.vendor_id == vendor_id}),
            ))
        return signals

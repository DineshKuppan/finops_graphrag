# main.py
import tempfile
from pathlib import Path

from src.domain import FinOpsContractGraph
from src.domain.base import MetaContext, Party
from src.domain.financials import FinancialTerm, PaymentSchedule
from src.domain.invoices import Invoice
from src.infrastructure.isolation_forest_detector import IsolationForestAnomalyDetector
from src.infrastructure.jsonl_feedback_store import JsonlFeedbackStore
from src.infrastructure.networkx_repo import NetworkXGraphRepository
from src.use_cases.detect_fraud import DetectFraudSignalsUseCase
from src.use_cases.fraud_rules import default_rules
from src.use_cases.ingest_doc import IngestDocumentUseCase
from src.use_cases.query_rag import QueryGraphRAGUseCase
from src.use_cases.review_feedback import RecordReviewFeedbackUseCase

# Real implementations are injected into placeholders here...
class MockExtractor:
    """Simulates real dynamic extraction: returns a canned document per raw text."""

    def __init__(self):
        buyer = Party(name="FinOps Corp", role="Customer")
        self.documents = {
            "contract": FinOpsContractGraph(
                ulid="contract_abc_123", title="Mock Subscription SLA", status="Active",
                context=MetaContext(domain="Subscription", doc_type="Vendor Contract"),
                parties=[Party(name="CloudCo, Inc.", role="Vendor", tax_id="12-3456789", bank_account="US-0001-4321"), buyer],
                financial_terms=[FinancialTerm(
                    name="Platform Fee", value=12_000,
                    payment_schedule=PaymentSchedule(frequency="Monthly", due_day=1, method="ACH"),
                )],
            ),
            "invoices": FinOpsContractGraph(
                ulid="invoice_batch_001", title="October AP batch", status="Received",
                context=MetaContext(domain="Subscription", doc_type="Invoice"),
                invoices=[
                    Invoice(invoice_number="CC-1001", vendor=Party(name="CloudCo Inc", role="Vendor"), bill_to=buyer,
                            amount=12_000, issue_date="2026-10-01", contract_ref="contract_abc_123", payment_method="ACH"),
                    # Same vendor, new bank account, wire transfer, inflated amount: payment-redirection pattern
                    Invoice(invoice_number="CC-1002", vendor=Party(name="CLOUDCO", role="Vendor"), bill_to=buyer,
                            amount=27_500, issue_date="2026-10-06", contract_ref="contract_abc_123",
                            payment_method="Wire", remit_to_account="US-0009-8765"),
                    # A "new" vendor sharing CloudCo's tax ID with no contract behind it: shell-vendor pattern
                    Invoice(invoice_number="CS-77", vendor=Party(name="Cloud Services Group", role="Vendor", tax_id="123456789"),
                            bill_to=buyer, amount=12_000, issue_date="2026-10-08"),
                ],
            ),
        }

    def extract_structured_data(self, text: str) -> FinOpsContractGraph:
        return self.documents["invoices" if "invoice" in text.lower() else "contract"]

def main(feedback_path: Path):
    print("🤖 Initializing FinOps GraphRAG Engine...")

    # 1. Initialize Adapters
    graph_storage = NetworkXGraphRepository()
    mock_extractor = MockExtractor() # Replace with your real OpenAI / Instructor Parser
    feedback_store = JsonlFeedbackStore(feedback_path)

    # 2. Inject Adapters into Application Usecases
    ingest_pipeline = IngestDocumentUseCase(extractor=mock_extractor, storage=graph_storage)
    query_pipeline = QueryGraphRAGUseCase(storage=graph_storage)
    # Vendor anomaly detection needs >= 8 invoicing vendors, so it stays silent on this small demo
    fraud_rules = default_rules(anomaly_detector=IsolationForestAnomalyDetector())
    fraud_pipeline = DetectFraudSignalsUseCase(reader=graph_storage, rules=fraud_rules, feedback=feedback_store)
    review_pipeline = RecordReviewFeedbackUseCase(store=feedback_store)

    # 3. Execute Operations
    for raw_document in ("Vendor Service Contract for SaaS Platform Cloud Subscription...", "October vendor invoice batch..."):
        doc_id = ingest_pipeline.execute(raw_document)
        print(f"✅ Successfully ingested document into Graph. Assigned ID: {doc_id}")

    context = query_pipeline.execute(domain="Subscription")
    print(f"📊 Retrieved RAG Context:\n{context}")

    assessment = fraud_pipeline.execute()
    print(f"\n🚨 Fraud Signals: {len(assessment.signals)}")
    for report in assessment.reports[:5]:
        print(f"  {report.score:.2f}  {report.entity_type:<8} {report.entity_id}")
    print(f"\n🧾 Explanation Prompt:\n{assessment.explanation_prompt}")

    # 4. Close the loop: a reviewer's verdict re-weights that rule on the next run
    drift = next(s for s in assessment.signals if s.rule_id == "PAYMENT_METHOD_DRIFT")
    review_pipeline.execute(drift, "DISMISSED", reviewer="ap-analyst", note="Wire approved by treasury")
    reassessment = fraud_pipeline.execute()
    print("\n🧑‍⚖️ Reviewer dismissed PAYMENT_METHOD_DRIFT:")
    print(next(line for line in reassessment.explanation_prompt.splitlines() if "PAYMENT_METHOD_DRIFT" in line))
    before = {r.entity_id: r.score for r in assessment.reports}
    for report in reassessment.reports[:5]:
        print(f"  {before[report.entity_id]:.3f} → {report.score:.3f}  {report.entity_type:<8} {report.entity_id}")

if __name__ == "__main__":
    # Use a persistent path in production so reviewer verdicts accumulate across runs
    with tempfile.TemporaryDirectory() as tmp:
        main(Path(tmp) / "fraud_feedback.jsonl")

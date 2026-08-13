# main.py
from src.infrastructure.networkx_repo import NetworkXGraphRepository
from src.use_cases.ingest_doc import IngestDocumentUseCase
from src.use_cases.query_rag import QueryGraphRAGUseCase

# Real implementations are injected into placeholders here...
class MockExtractor:
    def extract_structured_data(self, text: str):
        # Simulates real dynamic extraction schema return
        from src.domain.base import MetaContext
        class MockContract:
            ulid = "contract_abc_123"
            title = "Mock Subscription SLA"
            status = "Active"
            context = MetaContext(domain="Subscription", doc_type="Vendor Contract")
            parties = []
            clauses = []
            penalty_clauses = []
            lease_terms = []
            financial_terms = []
        return MockContract()

def main():
    print("🤖 Initializing FinOps GraphRAG Engine...")
    
    # 1. Initialize Adapters
    graph_storage = NetworkXGraphRepository()
    mock_extractor = MockExtractor() # Replace with your real OpenAI / Instructor Parser
    
    # 2. Inject Adapters into Application Usecases
    ingest_pipeline = IngestDocumentUseCase(extractor=mock_extractor, storage=graph_storage)
    query_pipeline = QueryGraphRAGUseCase(storage=graph_storage)
    
    # 3. Execute Operations
    raw_document = "Vendor Service Contract for SaaS Platform Cloud Subscription..."
    contract_id = ingest_pipeline.execute(raw_document)
    print(f"✅ Successfully ingested document into Graph. Assigned ID: {contract_id}")
    
    context = query_pipeline.execute(domain="Subscription")
    print(f"📊 Retrieved RAG Context:\n{context}")

if __name__ == "__main__":
    main()
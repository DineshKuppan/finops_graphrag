# src/use_cases/ingest_doc.py
from src.interfaces.llm_extractor import ILlmExtractor
from src.interfaces.graph_storage import IGraphStorage

class IngestDocumentUseCase:
    def __init__(self, extractor: ILlmExtractor, storage: IGraphStorage):
        # Dependencies are injected as abstract contracts (DIP)
        self.extractor = extractor
        self.storage = storage

    def execute(self, raw_text: str) -> str:
        if not raw_text.strip():
            raise ValueError("Document content cannot be empty.")
            
        # 1. Structure the unstructured document text
        structured_contract = self.extractor.extract_structured_data(raw_text)
        
        # 2. Add structural entities straight into the Knowledge Graph
        self.storage.save_contract_graph(structured_contract)
        
        return structured_contract.ulid
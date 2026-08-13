from typing import Literal
from src.interfaces.graph_storage import IGraphStorage

class QueryGraphRAGUseCase:
    def __init__(self, storage: IGraphStorage):
        self.storage = storage

    def execute(self, domain: Literal["REALTY", "Subscription"]) -> str:
        """
        Executes structural context harvesting across subgraphs before prompting your summary LLM.
        """
        # Step 1: Extract relational subgraphs strictly mapping your domain boundaries
        subgraph_context = self.storage.fetch_subgraph_context(domain_filter=domain)
        
        # Step 2: Decorate this structural representation into your standard generation workspace
        augmented_prompt = (
            f"### STRUCTURED GRAPH KNOWLEDGE ATTAINED ###\n"
            f"{subgraph_context}\n\n"
            f"Instruction: Based purely on the verified structural context constraints provided above, "
            f"synthesize an assessment profiling financial liabilities or optimization spaces."
        )
        return augmented_prompt
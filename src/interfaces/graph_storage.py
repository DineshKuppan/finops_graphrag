from abc import ABC, abstractmethod
from typing import Any, Literal

class IGraphStorage(ABC):
    @abstractmethod
    def save_contract_graph(self, contract_data: Any) -> None:
        """Persists parsed graph elements into the underlying engine."""
        pass

    @abstractmethod
    def fetch_subgraph_context(self, domain_filter: Literal["REALTY", "Subscription"]) -> str:
        """Retrieves structured context strings for targeted domains."""
        pass

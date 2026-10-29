from abc import ABC, abstractmethod
from src.domain.fraud import FraudGraphSnapshot

class IFraudGraphReader(ABC):
    @abstractmethod
    def fetch_fraud_snapshot(self) -> FraudGraphSnapshot:
        """Projects the graph into the plain records fraud rules evaluate."""
        pass

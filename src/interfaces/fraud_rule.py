from abc import ABC, abstractmethod
from typing import List
from src.domain.fraud import FraudGraphSnapshot, FraudSignal

class IFraudRule(ABC):
    @abstractmethod
    def evaluate(self, snapshot: FraudGraphSnapshot) -> List[FraudSignal]:
        """Returns every signal this rule finds; an empty list means nothing suspicious."""
        pass

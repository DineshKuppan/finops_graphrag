from abc import ABC, abstractmethod
from typing import List, Sequence

class IAnomalyDetector(ABC):
    @abstractmethod
    def score(self, rows: Sequence[Sequence[float]]) -> List[float]:
        """Scores each feature row from 0 (typical) to 1 (highly anomalous) relative to the others."""
        pass

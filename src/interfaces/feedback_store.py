from abc import ABC, abstractmethod
from typing import List
from src.domain.fraud import ReviewFeedback

class IFeedbackStore(ABC):
    @abstractmethod
    def record(self, feedback: ReviewFeedback) -> None:
        """Persists one reviewer verdict on a fraud signal."""
        pass

    @abstractmethod
    def list_feedback(self) -> List[ReviewFeedback]:
        """Returns every verdict recorded so far."""
        pass

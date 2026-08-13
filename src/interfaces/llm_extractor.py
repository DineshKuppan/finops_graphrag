from abc import ABC, abstractmethod
from typing import Any

class ILlmExtractor(ABC):
    @abstractmethod
    def extract_structured_data(self, text: str) -> Any:
        """Parses unstructured text down into specialized domains."""
        pass

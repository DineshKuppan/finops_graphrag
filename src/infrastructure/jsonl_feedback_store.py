from pathlib import Path
from typing import List, Union

from src.domain.fraud import ReviewFeedback
from src.interfaces.feedback_store import IFeedbackStore


class JsonlFeedbackStore(IFeedbackStore):
    """Append-only JSON Lines file: one verdict per line, so history is never rewritten."""

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)

    def record(self, feedback: ReviewFeedback) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(feedback.model_dump_json() + "\n")

    def list_feedback(self) -> List[ReviewFeedback]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as handle:
            return [ReviewFeedback.model_validate_json(line) for line in handle if line.strip()]

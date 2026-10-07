from dataclasses import dataclass

CLASSIFICATION_LEVELS = {
    "public": 0,
    "internal": 1,
    "confidential": 3,
    "restricted": 5,
}


@dataclass
class Invoice:
    """A mock FinOps resource (vendor invoice) that every access-control
    model in this lab is evaluated against."""

    id: str
    title: str
    department: str
    amount: float
    classification: str
    region: str
    owner_username: str

    @property
    def classification_level(self) -> int:
        return CLASSIFICATION_LEVELS.get(self.classification, 0)

    def public_view(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "department": self.department,
            "amount": self.amount,
            "classification": self.classification,
            "classification_level": self.classification_level,
            "region": self.region,
            "owner_username": self.owner_username,
        }

from datetime import date
from typing import Iterable, List, Optional
from src.domain.fraud import FraudGraphSnapshot

def parse_iso_date(value: Optional[str]) -> Optional[date]:
    try:
        return date.fromisoformat(value.strip())
    except (AttributeError, ValueError):
        return None

def mask(identifier: str) -> str:
    """Keeps only the last 4 characters: evidence is shown to reviewers and sent to an LLM."""
    return f"****{identifier[-4:]}" if len(identifier) > 4 else "****"

def docs_mentioning(snapshot: FraudGraphSnapshot, party_ids: Iterable[str]) -> List[str]:
    wanted = set(party_ids)
    docs = {c.contract_id for c in snapshot.contracts.values() if wanted & c.party_roles.keys()}
    docs |= {i.source_doc_id for i in snapshot.invoices if i.vendor_id in wanted}
    return sorted(docs)

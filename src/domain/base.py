from typing import Literal, Dict, Any, Optional
from pydantic import BaseModel, Field

class MetaContext(BaseModel):
    domain: Literal["REALTY", "Subscription"]
    doc_type: Literal["Invoice", "Bill", "Vendor Contract", "Customer Contract", "Office Lease"]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Party(BaseModel):
    name: str
    role: str
    tax_id: Optional[str] = None

class Clause(BaseModel):
    type: str
    text: str
    chunk_id: str

# FinOps GraphRAG Core Engine

A production-ready **GraphRAG (Retrieval-Augmented Generation)** pipeline architectural framework built in Python. This engine parses and organizes unstructured financial documents (Invoices, Bills, Vendor Contracts, and Office Leases) into explicit semantic subgraphs categorized into macro domains: **`REALTY`** and **`Subscription`**.

The repository strictly follows **SOLID design principles**, separating enterprise domain business models from infrastructure components (Graph Stores, LLM Parsers) using clean **Dependency Inversion** interfaces.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Architecture & Knowledge Graph](#architecture--knowledge-graph)
4. [Core Concepts](#core-concepts)
5. [Getting Started](#getting-started)
6. [API Reference](#api-reference)
7. [Extending the System](#extending-the-system)
8. [SOLID Compliance](#solid-compliance)
9. [Development & Testing](#development--testing)
10. [Troubleshooting](#troubleshooting)

---

## Project Overview

**Status**: ✅ Implemented (Core Framework) | 🚧 In Progress (Extended Ontologies)

The FinOps GraphRAG engine transforms unstructured financial documents into queryable knowledge graphs using:

- **Domain-Driven Design**: Three specialized ontology tracks for different contract aspects
- **Dependency Injection**: Pluggable extractors and storage backends
- **SOLID Principles**: Clean separation of business logic from infrastructure
- **Semantic Subgraphs**: Targeted knowledge retrieval for financial analysis

### Key Features

- 📊 **Multi-Domain Ontologies**: Penalties, Realty, and Financial terms
- 🔄 **Flexible Storage**: NetworkX in-memory or extensible to Neo4j, PostgreSQL
- 🤖 **LLM Integration**: LiteLLM/Instructor parser targeting local Llama models with schema-based extraction
- 🏗️ **Clean Architecture**: Zero infrastructure coupling in business logic
- 📐 **Semantic Graphs**: Structured relationships, not flat vector search

---

## Project Structure

```
finops_graphrag/
├── config/                      # ⚙️ Configuration & Environment loaders
│   └── settings.py
├── src/
│   ├── domain/                  # 📚 Enterprise Business Rules (Entities & Ontologies)
│   │   ├── __init__.py          # Root contract spec exporting FinOpsContractGraph
│   │   ├── base.py              # Shared definitions (Parties, Clauses, Metadata)
│   │   ├── penalties.py         # Penalty & Punitive Ontology Track
│   │   ├── realty.py            # Office Lease & Realty Ontology Track
│   │   └── financials.py        # Financial Terms Ontology Track
│   ├── interfaces/              # 🔌 Domain Inversion Abstractions (Agnostic Interfaces)
│   │   ├── __init__.py
│   │   ├── graph_storage.py     # IGraphStorage — Storage Boundary Contract
│   │   └── llm_extractor.py     # ILlmExtractor — LLM Parser Contract
│   ├── infrastructure/          # 🔧 Adapter Implementations (Low-Level Concrete Details)
│   │   ├── __init__.py
│   │   ├── networkx_repo.py     # Memory-backed MultiDiGraph via NetworkX
│   │   └── litellm_parser.py    # Structured output parsing via Instructor + LiteLLM proxy (local Llama)
│   └── use_cases/               # ⚡ Application Logic (Interactors/Orchestrators)
│       ├── __init__.py
│       ├── ingest_doc.py        # IngestDocumentUseCase — Extraction & Ingestion Flow
│       └── query_rag.py         # QueryGraphRAGUseCase — Subgraph Harvesting Flow
├── tests/                       # ✅ Isolated test suite
│   ├── __init__.py
│   ├── test_domain.py           # Domain model tests
│   └── test_use_cases.py        # Use case orchestration tests
├── main.py                      # 🚀 Composition Root & Application Entrypoint
├── pyproject.toml               # 📦 Project metadata & dependencies (uv-managed)
├── uv.lock                      # 🔒 Locked dependency versions
└── setup_project.sh             # 🔨 Project initialization script
```

---

## Architecture & Knowledge Graph

### Semantic Subgraph Model

Standard vector search loses semantic context across deeply relational data structures. This engine extracts and aligns structural information along **three distinct, domain-specific tracks**:

```
                    [ Domain: REALTY / SUBSCRIPTION ]
                                   │
                           (CATEGORIZED_AS)
                                   ▼
          ┌───────────────── [ Document ] ─────────────────┐
          │                        │                       │
   (HAS_INVOICE)              (HAS_BILL)            (IS_CONTRACT)
          ▼                        ▼                       ▼
     [ Invoice ]               [ Bill ]              [ Contract ]
                                                           │
         ┌─────────────────────────┼───────────────────────┴─────────────────────────┐
         ▼                         ▼                                                 ▼
  [ Penalty Clause ]         [ Lease Term ]                                   [ Financial Term ]
  • type, trigger, amount    • start, end, area_sqft                          • name, value, currency
         │                         │                                                 │
  (TRIGGERED_BY)              (HAS_RENT)                                        (SCHEDULES)
         ▼                         ▼                                                 ▼
   [ Breach Event ]         [ Rent Schedule ]                                [ Payment Schedule ]
  • condition, cure_period   • base, escalation, period                       • frequency, due_day, method
         │                         │                                                 │
    (QUANTIFIES)            (COVERS_PREMISES)                                      (CAPS)
         ▼                         ▼                                                 ▼
 [ Liquidated Damages ]       [ Premises ]                                    [ Liability Cap ]
  • cap, daily_rate          • floor, unit, fit_out                           • amount, basis
         │                         │                                                 │
   (ALLOWS_CURE)            (INCLUDES_CAM)                                       (SECURES)
         ▼                         ▼                                                 ▼
   [ Cure Period ]          [ CAM Charges ]                                  [ Security Deposit ]
  • days, remedy_action      • maintenance, annual_cap                        • amount, refund_terms
                                   │                                                 │
                              (HAS_OPTION)                                      (SUSPENDS)
                                   ▼                                                 ▼
                           [ Renewal Option ]                                 [ Force Majeure ]
                            • notice_by, term                                 • trigger, suspension_days
```

### Three Ontology Tracks

| Track | Purpose | Key Entities | Use Case |
|-------|---------|--------------|----------|
| **Penalties** | Breach & enforcement rules | Penalty Clauses, Breach Events, Liquidated Damages | Liability analysis, risk scoring |
| **Realty** | Property & occupancy terms | Lease Terms, Premises, Rent Schedules, CAM Charges | Real estate portfolio optimization |
| **Financials** | Payment & cost terms | Financial Terms, Payment Schedules, Liability Caps | Budget forecasting, cash flow modeling |

---

## Core Concepts

### Domain-Driven Design (DDD)

The project organizes all business logic into domain models (`src/domain/`) that are completely isolated from implementation details:

- **Domain Models** = Pure Pydantic schemas capturing business rules
- **Interfaces** = Contracts that infrastructure must fulfill
- **Use Cases** = Application orchestrators that compose domain + infrastructure

This separation ensures business logic is **testable, reusable, and technology-agnostic**.

### Dependency Inversion Principle (DIP)

High-level use cases never depend on concrete implementations:

```python
# ✅ GOOD: Use cases depend on abstractions
class IngestDocumentUseCase:
    def __init__(self, extractor: ILlmExtractor, storage: IGraphStorage):
        self.extractor = extractor  # Could be OpenAI, Claude, Ollama...
        self.storage = storage       # Could be NetworkX, Neo4j, PostgreSQL...

# ❌ BAD: Would couple to concrete implementation
# def __init__(self, extractor: LiteLLMInstructorExtractor, storage: NetworkXGraphRepository):
```

This design lets you **swap implementations without changing business logic**. Test with a mock extractor, deploy against a local Llama model via LiteLLM, scale to Neo4j later—all without touching use cases.

### Three Ontology Tracks

Each domain track represents a distinct aspect of financial contracts:

- **Penalties Track** (`src/domain/penalties.py`): Breach conditions, cure periods, liquidated damages
- **Realty Track** (`src/domain/realty.py`): Lease terms, premises details, rent schedules, CAM charges
- **Financials Track** (`src/domain/financials.py`): Payment terms, financial metrics, liability caps

Each track can be queried independently via `QueryGraphRAGUseCase` with domain filtering.

---

## Getting Started

### 1. Prerequisites

- **[uv](https://docs.astral.sh/uv/)** for dependency management and Python execution (verify with `uv --version`)
- **Python 3.10+** — uv will download and pin an interpreter automatically if none is found
- **A running [LiteLLM proxy](https://docs.litellm.ai/docs/proxy/quick_start)** in front of a local Llama model, e.g. via [Ollama](https://ollama.com/) (for LLM-based extraction; optional for mock mode)

Install uv if you don't have it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Install Dependencies

```bash
cd finops_graphrag
uv sync
```

`uv sync` reads `pyproject.toml`/`uv.lock`, creates a `.venv`, and installs all runtime + dev dependencies in one step.

Verify installation:
```bash
uv run python -c "import networkx, pydantic, openai; print('✅ All dependencies installed')"
```

### 3. Environment Configuration

This engine talks to local Llama models through a [LiteLLM proxy](https://docs.litellm.ai/docs/proxy/quick_start), not the OpenAI API directly. `litellm[proxy]` lives in its own `proxy` dependency group (it pulls in ~65 packages — FastAPI, boto3, etc. — that the app itself never imports), so install it only when you need to run the proxy locally:

```bash
uv sync --group proxy
```

> **Platform note**: pinned to `litellm<1.92` — 1.92+ ships a Rust extension with wheels only for Linux, which fails to build from source on macOS without a modern Cargo toolchain.

Then start a proxy in front of your local models (e.g. Ollama):

```bash
cat << 'EOF' > litellm_config.yaml
model_list:
  - model_name: llama3
    litellm_params:
      model: ollama/llama3
      api_base: http://localhost:11434
EOF

uv run --group proxy litellm --config litellm_config.yaml --port 4000
```

Point the extractor at the running proxy via environment variables (or pass them directly to `LiteLLMInstructorExtractor`):

```bash
# .env
LITELLM_PROXY_URL="http://localhost:4000"
LITELLM_API_KEY="sk-local"   # placeholder unless you've enabled proxy auth
```

### 4. Running the Framework

**Option A: Using Mock Extractor (No LiteLLM Proxy Required)**

```bash
uv run python main.py
```

This runs with the built-in `MockExtractor` class in `main.py`, which simulates LLM parsing without external calls.

**Option B: Using the Local Llama Parser (via LiteLLM)**

Edit `main.py` to replace `MockExtractor` with `LiteLLMInstructorExtractor`:

```python
from src.infrastructure.litellm_parser import LiteLLMInstructorExtractor

# In main():
parser = LiteLLMInstructorExtractor(model="llama3")  # Reads LITELLM_PROXY_URL / LITELLM_API_KEY from environment
ingest_pipeline = IngestDocumentUseCase(extractor=parser, storage=graph_storage)
```

### 5. Example: Basic Usage

```python
from src.infrastructure.networkx_repo import NetworkXGraphRepository
from src.use_cases.ingest_doc import IngestDocumentUseCase
from src.use_cases.query_rag import QueryGraphRAGUseCase
from src.infrastructure.litellm_parser import LiteLLMInstructorExtractor  # or MockExtractor

# Initialize components
storage = NetworkXGraphRepository()
extractor = LiteLLMInstructorExtractor(model="llama3")  # Or MockExtractor for testing

# Create use cases
ingest_use_case = IngestDocumentUseCase(extractor=extractor, storage=storage)
query_use_case = QueryGraphRAGUseCase(storage=storage)

# Ingest a document
document_text = """
    Vendor Service Agreement: CloudPlatform SaaS
    Effective Date: 2024-01-15
    Termination Clause: Either party may terminate with 30 days notice...
    Liability Cap: USD 50,000 per incident
"""
contract_id = ingest_use_case.execute(document_text)
print(f"✅ Ingested as: {contract_id}")

# Query the graph for financial terms
rag_context = query_use_case.execute(domain="Subscription")
print(f"📊 RAG Context:\n{rag_context}")
```

### 6. Verification

After running `main.py`, verify:
- ✅ Application starts without errors
- ✅ Document is ingested (contract ID is printed)
- ✅ RAG context is retrieved and printed
- ✅ No LiteLLM proxy connection errors if using mock mode

If you see `Contract Object:` output, the graph ingestion succeeded!

---

## API Reference

### Core Use Cases

#### `IngestDocumentUseCase`
**File**: `src/use_cases/ingest_doc.py`

Orchestrates the parsing and storage of unstructured documents into the knowledge graph.

```python
class IngestDocumentUseCase:
    def __init__(self, extractor: ILlmExtractor, storage: IGraphStorage):
        """
        Args:
            extractor: LLM parser implementing ILlmExtractor
            storage: Graph database implementing IGraphStorage
        """
        pass

    def execute(self, raw_text: str) -> str:
        """
        Parses unstructured text and stores as graph nodes.
        
        Returns:
            Contract ULID (Universally Unique Lexicographically Sortable Identifier)
        
        Raises:
            ValueError: If raw_text is empty
        """
        pass
```

#### `QueryGraphRAGUseCase`
**File**: `src/use_cases/query_rag.py`

Retrieves domain-specific subgraphs and augments prompts with structured context.

```python
class QueryGraphRAGUseCase:
    def __init__(self, storage: IGraphStorage):
        pass

    def execute(self, domain: Literal["REALTY", "Subscription"]) -> str:
        """
        Fetches all contracts in a domain and returns structured context.
        
        Args:
            domain: Either "REALTY" or "Subscription"
        
        Returns:
            Formatted string containing graph context (ready for LLM augmentation)
        """
        pass
```

### Core Interfaces

#### `IGraphStorage`
**File**: `src/interfaces/graph_storage.py`

Contract for storing and retrieving graph data. Implement this to add new storage backends (Neo4j, PostgreSQL, etc.).

```python
class IGraphStorage(ABC):
    @abstractmethod
    def save_contract_graph(self, contract_data: Any) -> None:
        """Persists parsed graph elements into the underlying engine."""
        pass

    @abstractmethod
    def fetch_subgraph_context(self, domain_filter: Literal["REALTY", "Subscription"]) -> str:
        """Retrieves structured context strings for targeted domains."""
        pass
```

#### `ILlmExtractor`
**File**: `src/interfaces/llm_extractor.py`

Contract for structured data extraction. Implement this to swap extractors (OpenAI, Claude, Ollama, etc.).

```python
class ILlmExtractor(ABC):
    @abstractmethod
    def extract_structured_data(self, text: str) -> Any:
        """Parses unstructured text into FinOpsContractGraph domain model."""
        pass
```

### Domain Models

#### `FinOpsContractGraph`
**File**: `src/domain/__init__.py`

Root contract entity representing a parsed financial document.

```python
class FinOpsContractGraph(BaseModel):
    ulid: str                               # Unique identifier
    title: str                              # Document title
    status: str                             # Active, Inactive, Archived, etc.
    context: MetaContext                    # Domain & document type
    parties: List[Party]                    # Signatories
    clauses: List[Clause]                   # General clauses
    
    # Domain-specific ontologies
    penalty_clauses: List[PenaltyClause]    # Breach & enforcement
    lease_terms: List[LeaseTerm]            # Property & occupancy
    financial_terms: List[FinancialTerm]    # Payments & costs
```

#### `MetaContext`
**File**: `src/domain/base.py`

Metadata classifying the document domain and type.

```python
class MetaContext(BaseModel):
    domain: Literal["REALTY", "Subscription"]  # Contract domain
    doc_type: Literal["Invoice", "Bill", "Vendor Contract", ...]  # Document type
    metadata: Dict[str, Any]                    # Custom metadata
```

#### `Party`
**File**: `src/domain/base.py`

Represents a signatory to the contract.

```python
class Party(BaseModel):
    name: str                   # Entity name
    role: str                   # Signatory role (Lessor, Tenant, Vendor, etc.)
    tax_id: Optional[str]       # Tax ID or business registration number
```

#### `LeaseTerm`
**File**: `src/domain/realty.py`

Captures lease duration, area, and rental arrangements.

```python
class LeaseTerm(BaseModel):
    start_date: str             # ISO format date
    end_date: str               # ISO format date
    area_sqft: float            # Rentable square footage
    rent_schedule: Optional[RentSchedule]  # Base rent, escalation, period
```

#### `FinancialTerm`
**File**: `src/domain/financials.py`

Represents a financial metric or payment term.

```python
class FinancialTerm(BaseModel):
    name: str                   # Term name (e.g., "Liability Cap", "Annual Fee")
    value: float                # Numeric value
    currency: str               # ISO currency code (USD, EUR, etc.)
```

---

## Extending the System

### Adding a New Storage Backend

Add the driver dependency with uv:

```bash
uv add neo4j
```

Implement `IGraphStorage` to support a new database:

```python
# src/infrastructure/neo4j_repo.py
from neo4j import GraphDatabase
from src.interfaces.graph_storage import IGraphStorage

class Neo4jGraphRepository(IGraphStorage):
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def save_contract_graph(self, contract_data: Any) -> None:
        """Push contract graph nodes and relationships to Neo4j"""
        with self.driver.session() as session:
            # Create nodes and relationships via Cypher queries
            pass

    def fetch_subgraph_context(self, domain_filter: Literal["REALTY", "Subscription"]) -> str:
        """Query Neo4j for domain-specific subgraphs"""
        with self.driver.session() as session:
            # Cypher query to retrieve context
            pass
```

Then inject it into your use cases:

```python
storage = Neo4jGraphRepository(uri="bolt://localhost:7687", user="neo4j", password="...")
ingest_pipeline = IngestDocumentUseCase(extractor=parser, storage=storage)
```

### Adding a New LLM Extractor

Add the SDK dependency with uv:

```bash
uv add anthropic
```

Implement `ILlmExtractor` to support a new language model:

```python
# src/infrastructure/claude_parser.py
from anthropic import Anthropic
from src.interfaces.llm_extractor import ILlmExtractor
from src.domain import FinOpsContractGraph

class ClaudeExtractor(ILlmExtractor):
    def __init__(self, api_key: str = None):
        self.client = Anthropic(api_key=api_key)

    def extract_structured_data(self, text: str) -> FinOpsContractGraph:
        """Use Claude to parse documents with JSON schema guidance"""
        prompt = f"""
        Extract financial contract data from the following document.
        Return structured JSON matching this schema:
        {FinOpsContractGraph.model_json_schema()}
        
        Document:
        {text}
        """
        
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response and validate against FinOpsContractGraph
        return FinOpsContractGraph.model_validate_json(response.content[0].text)
```

Inject it into your pipeline:

```python
parser = ClaudeExtractor(api_key=os.getenv("ANTHROPIC_API_KEY"))
ingest_pipeline = IngestDocumentUseCase(extractor=parser, storage=storage)
```

### Adding a New Ontology Track

Create a new domain model and integrate it into the graph:

```python
# src/domain/compliance.py
from pydantic import BaseModel
from typing import List

class ComplianceClause(BaseModel):
    requirement: str            # Compliance requirement
    standard: str               # Standard (ISO, SOC2, HIPAA, etc.)
    deadline: str               # Deadline for compliance

class ComplianceTrack(BaseModel):
    clauses: List[ComplianceClause]

# Update src/domain/__init__.py
from src.domain.compliance import ComplianceTrack

class FinOpsContractGraph(BaseModel):
    # ... existing fields ...
    compliance_clauses: List[ComplianceClause] = Field(default_factory=list)

# Update src/infrastructure/networkx_repo.py
def save_contract_graph(self, contract_data: FinOpsContractGraph) -> None:
    # ... existing code ...
    for idx, cc in enumerate(contract_data.compliance_clauses):
        cc_id = f"compliance_{c_id}_{idx}"
        self.graph.add_node(cc_id, type="ComplianceClause", 
                          requirement=cc.requirement, standard=cc.standard)
        self.graph.add_edge(c_id, cc_id, relation="HAS_COMPLIANCE")
```

---

## SOLID Compliance

The engine strictly adheres to SOLID design principles:

### S — Single Responsibility Principle
Each class has one reason to change:
- `IngestDocumentUseCase` (file: `src/use_cases/ingest_doc.py`) — only changes when ingestion flow changes
- `NetworkXGraphRepository` (file: `src/infrastructure/networkx_repo.py`) — only changes when storage logic changes
- `MetaContext` (file: `src/domain/base.py`) — only changes when metadata schema changes

### O — Open/Closed Principle
The system is open for extension, closed for modification:
- Add new ontology tracks by creating new domain files (no changes to existing code)
- Add new extractors by implementing `ILlmExtractor` (no changes to use cases)
- Extend metadata in `MetaContext` without breaking graph operations

### L — Liskov Substitution Principle
Any storage backend implementing `IGraphStorage` is transparently swappable:
```python
# Both of these work identically from the use case perspective
storage = NetworkXGraphRepository()  # In-memory graphs
storage = Neo4jGraphRepository(...)  # Neo4j backend
# Use case code never changes
```

### I — Interface Segregation Principle
Components depend only on methods they actually call:
- `IngestDocumentUseCase` only calls `extract_structured_data()` on extractors
- `QueryGraphRAGUseCase` only calls `fetch_subgraph_context()` on storage
- Clients never depend on unused methods

### D — Dependency Inversion Principle
High-level modules depend on abstractions, not concrete implementations:
- **Use cases** depend on `ILlmExtractor` and `IGraphStorage` interfaces
- **Infrastructure** implementations (`LiteLLMInstructorExtractor`, `NetworkXGraphRepository`) depend on interfaces
- **Business logic** never imports infrastructure code directly

This creates a **unidirectional dependency flow**: Domain ← Interfaces ← Infrastructure

---

## Development & Testing

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_domain.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

### Test Structure

- **`tests/test_domain.py`**: Domain model validation (schemas, constraints, business rules)
- **`tests/test_use_cases.py`**: Use case orchestration (end-to-end flows with mocks)

### Writing Tests

Example: Testing ingestion with a mock extractor

```python
# tests/test_use_cases.py
import pytest
from unittest.mock import Mock
from src.use_cases.ingest_doc import IngestDocumentUseCase
from src.domain import FinOpsContractGraph

def test_ingest_document_success():
    # Setup mocks
    mock_extractor = Mock()
    mock_storage = Mock()
    
    mock_contract = FinOpsContractGraph(
        ulid="test_123",
        title="Test Contract",
        status="Active",
        context=MetaContext(domain="Subscription", doc_type="Vendor Contract"),
        parties=[],
        clauses=[]
    )
    mock_extractor.extract_structured_data.return_value = mock_contract
    
    # Execute
    use_case = IngestDocumentUseCase(extractor=mock_extractor, storage=mock_storage)
    result = use_case.execute("Test document text")
    
    # Assert
    assert result == "test_123"
    mock_storage.save_contract_graph.assert_called_once()

def test_ingest_document_empty_text():
    mock_extractor = Mock()
    mock_storage = Mock()
    use_case = IngestDocumentUseCase(extractor=mock_extractor, storage=mock_storage)
    
    with pytest.raises(ValueError, match="cannot be empty"):
        use_case.execute("")
```

### Project Development Workflow

1. **Add feature branch**: `git checkout -b feature/new-ontology`
2. **Implement domain model**: Add Pydantic schema to `src/domain/`
3. **Add infrastructure adapter**: Implement storage/extractor if needed
4. **Write tests**: Cover domain + use case logic
5. **Run tests**: Ensure all pass
6. **Integrate with main.py**: Wire up and test end-to-end

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'src'`

**Solution**: Ensure you're running from the project root:
```bash
cd /path/to/finops_graphrag
uv run python main.py
```

### Issue: `openai.APIConnectionError` / `Connection refused` when using `LiteLLMInstructorExtractor`

**Solution**: The LiteLLM proxy isn't reachable. Verify it's running and the URL is correct:
```bash
curl http://localhost:4000/health   # or your LITELLM_PROXY_URL
echo $LITELLM_PROXY_URL             # confirm it's set if not using the default
```
If the proxy isn't running, start it (see [Environment Configuration](#getting-started)):
```bash
uv run --group proxy litellm --config litellm_config.yaml --port 4000
```

### Issue: `pydantic_core._pydantic_core.ValidationError: validation error for FinOpsContractGraph`

**Solution**: The extracted data doesn't match the schema. Check:
1. LLM output format (should be valid JSON matching the schema)
2. Required fields are present: `ulid`, `title`, `status`, `context`
3. Domain value is one of: `"REALTY"` or `"Subscription"`

### Issue: Graph queries return "No active sub-graph data found"

**Solution**: 
- Verify documents were ingested: Check `graph.nodes()` in debugger
- Ensure domain filter matches document context: Use `"REALTY"` or `"Subscription"` exactly
- Confirm the context node was created: Check `graph.out_edges(contract_id)`

### Issue: Tests fail with import errors

**Solution**: Ensure the package structure is correct:
```bash
uv run python -c "from src.domain import FinOpsContractGraph; print('✅ Import works')"
```

`uv run` always executes from the project root's `.venv` with the project directory on `sys.path`, so `PYTHONPATH` tweaks shouldn't be necessary. If imports still fail, re-sync the environment:
```bash
uv sync --reinstall
```

### Issue: `uv.lock` is out of sync with `pyproject.toml`

**Solution**: Regenerate the lockfile and re-sync:
```bash
uv lock
uv sync
```

---

## License & Contributing

This project is maintained as a reference implementation for clean architecture in financial document processing.

For questions or contributions, please refer to the project maintainers.

**Last Updated**: 2026-07-12
**Python Version**: 3.10+
**Dependency Manager**: [uv](https://docs.astral.sh/uv/)
**Core Dependencies**: pydantic, networkx, openai, instructor, python-dotenv

# Spec: Graph-Based Fraud Signal Detection

| | |
|---|---|
| **Status** | Phases 1–3 implemented · Phase 4 proposed |
| **Author** | Dineshkumar Kuppan |
| **Date** | 2026-10-29 |

## 1. Problem

The engine turns contracts, leases and invoices into a knowledge graph, but nobody
reads that graph for **fraud**. Most AP/vendor fraud does not show up in a single document.
It shows up in how documents relate: two "different" vendors paid into one bank
account, an invoice that bills against an expired contract, a lease unit rented twice.
The graph already holds these relationships, so it is a good place to look for them.

The current ingestion also drops the data fraud detection needs:

1. `Party.tax_id` is extracted but never written to the graph.
2. Party nodes are keyed on the raw name, so `"ACME, Inc."` and `"Acme Inc"` become two
   vendors. Splitting one vendor across name variants is how shell vendors avoid detection.
3. Payment method, remittance bank accounts and invoices are not modelled at all.

## 2. Goals / Non-goals

**Goals**
- Find **explainable** fraud *signals*: each signal names the rule, a severity, the
  graph entities involved, and the source documents.
- Rank parties, contracts and invoices by a bounded risk score (0–1).
- Produce an LLM prompt that *explains* the signals. The LLM never *decides* fraud.
- Keep detection independent of the storage backend, with each rule testable on its own.

**Non-goals**
- Deciding that something is fraud. The output is a review queue for a human.
- Real-time or streaming detection. This runs as a batch over the graph.
- Statistical/ML anomaly detection (proposed as Phase 4).

## 3. Design

### 3.1 Domain changes (`src/domain`)

| Change | File |
|---|---|
| `Party.bank_account: Optional[str]` | `base.py` |
| New `Invoice` model (number, vendor, bill_to, amount, currency, issue_date, contract_ref, payment_method, remit_to_account) | `invoices.py` |
| `FinOpsContractGraph.invoices: List[Invoice]` | `__init__.py` |
| `canonical_party_key()` / `canonical_identifier()`: pure normalisation helpers | `identity.py` |
| `FraudSignal`, `RiskReport`, `FraudAssessment`, and a read-only `FraudGraphSnapshot` | `fraud.py` |

**Entity resolution.** `canonical_party_key` applies Unicode folding, lowercases,
turns `&` into `and`, strips punctuation, and removes trailing legal suffixes
(`inc`, `llc`, `ltd`, `gmbh`, …). `"ACME, Inc."`, `"Acme Inc"` and `"acme"` all resolve to
`party_acme`. Tax IDs and bank accounts are normalised to uppercase alphanumerics.

### 3.2 Graph schema additions

```
(Party)-[IDENTIFIED_BY {declared_in}]->(TaxId)
(Party)-[PAID_TO {declared_in}]->(BankAccount)
(Contract)-[PARTY_TO {role}]->(Party)            # role moved onto the edge
(Contract)-[CONTAINS_INVOICE]->(Invoice)
(Invoice)-[ISSUED_BY]->(Party)
(Invoice)-[BILLED_TO]->(Party)
(Invoice)-[BILLED_UNDER]->(Contract)            # may point at a not-yet-ingested ULID
(Invoice)-[REMIT_TO]->(BankAccount)
```

`FinancialTerm` nodes now carry `currency`, `frequency` and `payment_method`. `LeaseTerm`
nodes carry `floor` and `unit`.

`declared_in` records which document asserted an identifier. Payment drift depends on it:
the account a *contract* declares is trusted, and the account an *invoice* asks to be
paid into is checked against it.

### 3.3 Read port (`src/interfaces/fraud_graph_reader.py`)

```python
class IFraudGraphReader(ABC):
    def fetch_fraud_snapshot(self) -> FraudGraphSnapshot: ...
```

This is a separate interface from `IGraphStorage` (ISP), so storage backends that do no
fraud detection don't have to implement it. The snapshot is plain pydantic records
(parties, contracts, invoices), so rules never touch NetworkX or Cypher. A Neo4j adapter
would only need to build the same snapshot.

### 3.4 Rules (`src/interfaces/fraud_rule.py`, `src/use_cases/fraud_rules/`)

```python
class IFraudRule(ABC):
    def evaluate(self, snapshot: FraudGraphSnapshot) -> List[FraudSignal]: ...
```

| Signal ID | Pattern | Severity | Phase |
|---|---|---|---|
| `SHARED_BANK_ACCOUNT` | ≥2 distinct parties declare, or invoice remittance points to, the same account | HIGH | 2 |
| `SHARED_TAX_ID` | ≥2 distinct parties declare the same tax ID | HIGH | 2 |
| `DUPLICATE_INVOICE_NUMBER` | Same vendor, same invoice number, different documents | HIGH | 2 |
| `DUPLICATE_AMOUNT` | Same vendor, amount and currency, issue dates < 14 days apart | MEDIUM | 2 |
| `CONTRACT_OVERBILLING` | Invoice amount > largest priced `FinancialTerm` of its contract (HIGH if ≥ 2×) | MEDIUM/HIGH | 2 |
| `ORPHAN_INVOICE` | No contract reference (MEDIUM), unknown contract (HIGH), inactive contract (HIGH), or vendor not party to the contract (HIGH) | MEDIUM/HIGH | 3 |
| `PAYMENT_METHOD_DRIFT` | Invoice method not in the contract's `PaymentSchedule` methods | MEDIUM | 3 |
| `REMITTANCE_ACCOUNT_DRIFT` | Invoice remit-to account differs from the account the contract declares for that vendor | HIGH | 3 |
| `LEASE_OVERLAP` | Different contracts with the same landlord/lessor lease the same floor + unit for overlapping dates | HIGH | 3 |
| `CIRCULAR_FLOW` | Payer→payee cycle of length 3–6 across invoices (round-tripping) | MEDIUM | 3 |

Thresholds (window days, tolerance, cycle lengths) are constructor arguments.
Bank accounts and tax IDs are **masked to their last 4 characters** in evidence text,
because that text is passed to an LLM and shown to reviewers.

### 3.5 Use case (`src/use_cases/detect_fraud.py`)

`DetectFraudSignalsUseCase(reader, rules).execute() -> FraudAssessment`

1. Read the snapshot through `IFraudGraphReader`.
2. Run every injected rule. Concrete rules are chosen at the composition root
   (`main.py` → `default_rules()`), so the use case depends only on `IFraudRule`.
3. **Scoring:** each signal is evidence against every entity it names. Severity weights
   are LOW 0.2, MEDIUM 0.5, HIGH 0.8, combined as a noisy-OR:
   `score = 1 − Π(1 − wᵢ)`. The score stays within [0, 1], rises with more independent
   evidence, and can be traced back to specific signals.
4. **Explanation prompt:** in the same style as `QueryGraphRAGUseCase`, signals and the
   ranking are rendered into a prompt. It tells the LLM to explain each risk, give
   plausible legitimate explanations, and suggest verification steps, using only the
   facts listed and without calling anything confirmed fraud.

## 4. Phases

| Phase | Scope | Status |
|---|---|---|
| **1. Data foundation** | Domain additions, entity resolution, identifier/invoice nodes, extractor prompt | ✅ |
| **2. Engine + core rules** | Snapshot port, `IFraudRule`, shared identifiers, duplicate billing, overbilling, use case + scoring + prompt | ✅ |
| **3. Extended rules** | Orphan invoice, payment/remittance drift, lease overlap, circular flow, `main.py` demo | ✅ |
| **4. Graph ML (proposed)** | Node2Vec embeddings + isolation forest for unusual vendors that no rule covers; reviewer feedback loop to tune weights | ⏳ |

## 5. Testing

- `tests/test_identity.py`: normalisation edge cases.
- `tests/test_graph_repository.py`: entity resolution and the snapshot built from ingested docs.
- `tests/test_fraud_rules.py`: one positive and at least one negative case per rule, built
  from real `FinOpsContractGraph` documents ingested into the NetworkX repo.
- `tests/test_detect_fraud.py`: scoring maths, ranking, prompt contents and masking.

Run with `uv run pytest tests`.

## 6. Known limitations

- **Overbilling is per-invoice.** Cumulative billing against a contract's total value
  needs term duration and frequency semantics that the ontology doesn't model yet.
  Currency mismatches are not converted.
- **Entity resolution is lexical.** It will not merge `"IBM"` with
  `"International Business Machines"`. Fuzzy or LLM-assisted resolution is a follow-up.
- **Lease overlap needs extracted premises.** Without floor/unit and a landlord/lessor
  role, the rule skips the lease rather than guess, because a building address is not
  modelled.
- **Status matching is a deny-list** (`terminated`, `expired`, …). Unknown statuses are
  treated as active to avoid false positives.
- The snapshot loads the whole graph into memory. That is fine for NetworkX, but a Neo4j
  adapter should push rule patterns down into Cypher once volumes grow.

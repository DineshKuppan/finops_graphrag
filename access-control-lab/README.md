# FinOps Access Control Lab

A small, self-contained lab for exploring and comparing three authorization
models — **RBAC**, **ABAC**, and **PBAC** — against the *same* users and the
*same* mock FinOps resources (vendor invoices), so the differences between
the models are visible side by side instead of theoretical.

- **Backend**: Python 3.12 + FastAPI, JWT auth, three independent
  access-control engines over an in-memory dataset.
- **Frontend**: Next.js 16 (App Router, TypeScript), a "pick a demo user"
  login flow and three model-comparison screens.
- **Dockerized**: each service has its own `Dockerfile`; `docker-compose.yml`
  runs both together.

This is a teaching/exploration tool, not a production authorization
framework — there's no real database, and all passwords are the same demo
password (clearly labeled as such).

---

## The three models, explained via this lab

Every model answers the same question — *"can this user view or approve
this invoice?"* — but each is given different inputs:

| Model | Decides from | What it's good at | What it misses |
|---|---|---|---|
| **RBAC** | Only the user's **roles**, via a static role→permission matrix (`app/access_control/rbac.py`) | Simple, auditable, fast to reason about | No notion of *which* invoice — a `finance_manager` can approve every invoice, an `employee` can view none, even their own department's |
| **ABAC** | **Attributes** of the user (department, clearance, region) compared against attributes of the resource (department, classification, amount) (`app/access_control/abac.py`) | Fine-grained, scoped per-resource, same role gets different answers on different resources | Rules are still hard-coded in Python |
| **PBAC** | Declarative **policy documents** (`app/access_control/policies/finops_policies.json`) that can mix roles, attributes, *and* environment/context (e.g. time of day), combined with a deny-overrides algorithm | Generalizes RBAC + ABAC, externalizes rules as data, supports explicit deny rules and context-awareness | More moving parts to reason about; conflicting policies need a combining algorithm (here: deny-overrides, default-deny) |

The PBAC screen lets you flip a **"simulate after-hours"** toggle — the same
user, resource, and role suddenly get a different answer purely because of
an environment attribute (`environment.business_hours`), which only PBAC's
policy set accounts for.

### The demo data

Five users, each with a role (for RBAC) and attributes (for ABAC/PBAC):

| Username | Role | Department | Clearance | Region |
|---|---|---|---|---|
| `alice_admin` | admin | IT | 5 | US |
| `bob_finance` | finance_manager | FINANCE | 3 | US |
| `carol_auditor` | auditor | FINANCE | 4 | EU |
| `dave_marketing` | employee | MARKETING | 1 | US |
| `erin_legal` | employee | LEGAL | 2 | EU |

All passwords are `password123`.

Seven mock invoices across departments, classifications (`internal`,
`confidential`, `restricted`) and regions — see
`backend/app/db/seed_data.py`. Try, for example:

- Log in as `bob_finance` and compare the **RBAC** tab (sees/approves
  everything, including other departments' invoices) against **ABAC**/
  **PBAC** (scoped to FINANCE, and blocked from the `restricted` invoice
  because his clearance is too low).
- Log in as `dave_marketing` (an `employee`) and compare **RBAC** (can view
  *nothing* — the role has no invoice permissions) against **ABAC**/**PBAC**
  (can view his own department's invoices).
- On the **PBAC** tab, click "show raw policies" to see the actual JSON
  rules being evaluated, and "why?" on any row to see the full evaluation
  trace.

---

## Project structure

```
access-control-lab/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt / requirements-dev.txt
│   ├── app/
│   │   ├── main.py                 # FastAPI app + CORS
│   │   ├── core/                   # config, JWT + password hashing
│   │   ├── models/                 # User, Invoice dataclasses
│   │   ├── db/seed_data.py         # in-memory demo users & invoices
│   │   ├── schemas/                # pydantic request/response models
│   │   ├── access_control/
│   │   │   ├── rbac.py             # role -> permission matrix
│   │   │   ├── abac.py             # attribute comparison rules
│   │   │   ├── pbac.py             # generic policy engine
│   │   │   └── policies/finops_policies.json
│   │   └── api/routes/             # auth, rbac_demo, abac_demo, pbac_demo
│   └── tests/                      # pytest unit + API tests
└── frontend/
    ├── Dockerfile
    ├── app/                        # Next.js App Router pages
    │   ├── login/, dashboard/, rbac/, abac/, pbac/
    ├── components/                 # NavBar, ModelTabs, InvoiceTable, RequireAuth
    └── lib/                        # typed API client + auth context
```

---

## Running it

### With Docker Compose (recommended)

```bash
cd access-control-lab
cp .env.example .env   # optional, defaults work out of the box
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:3000

> **Note on this environment**: the sandbox this lab was built in has no
> Docker daemon available, so the `docker compose up` path itself could not
> be executed here. Both Dockerfiles were written against the standard
> patterns for FastAPI (`python:3.12-slim` + `pip install`) and Next.js
> (`node:20-alpine` multi-stage build using `output: "standalone"`), and the
> application they package was fully verified by running the backend
> (`uvicorn`) and frontend (`next build && next start`) directly, including
> an end-to-end browser test (see "Testing" below). Please run
> `docker compose up --build` once to confirm the images build cleanly in
> your environment, and let me know if anything needs adjusting.

### Without Docker

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Then open http://localhost:3000.

---

## API reference (backend)

All routes except `/health` and `/auth/*` require `Authorization: Bearer <token>`.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/auth/users` | List demo users (for the login picker) |
| POST | `/auth/login` | `{username, password}` → `{access_token}` |
| GET | `/auth/me` | Current user's profile (roles + attributes) |
| GET | `/{rbac\|abac\|pbac}/invoices` | All invoices + a view decision under that model |
| POST | `/{rbac\|abac\|pbac}/invoices/{id}/approve` | Approve decision under that model |
| GET | `/pbac/policies` | Raw PBAC policy documents |

`GET`/`POST` under `/pbac/...` accept `?simulate_after_hours=true` to force
the context-aware deny policy to trigger.

---

## Testing

Backend unit + API tests (22 tests covering each model's edge cases plus
the HTTP layer):

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

The frontend was exercised end-to-end with a headless-browser script
(login → dashboard → RBAC/PBAC tables → approve → toggle after-hours →
verify the badge flips from ALLOWED to DENIED) with zero console errors;
it isn't checked into the repo since it's a one-off verification script,
not part of the app.

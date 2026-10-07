from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _token(username: str) -> str:
    r = client.post("/auth/login", json={"username": username, "password": "password123"})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_login_wrong_password_rejected():
    r = client.post("/auth/login", json={"username": "alice_admin", "password": "nope"})
    assert r.status_code == 401


def test_unauthenticated_requests_are_rejected():
    assert client.get("/auth/me").status_code == 401
    assert client.get("/rbac/invoices").status_code == 401
    assert client.get("/abac/invoices").status_code == 401
    assert client.get("/pbac/invoices").status_code == 401


def test_full_login_and_decision_flow():
    token = _token("bob_finance")
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/auth/me", headers=headers).json()
    assert me["roles"] == ["finance_manager"]

    for model in ("rbac", "abac", "pbac"):
        r = client.get(f"/{model}/invoices", headers=headers)
        assert r.status_code == 200
        assert len(r.json()) == 7  # every model evaluates every invoice


def test_pbac_policies_endpoint_exposes_raw_policies():
    r = client.get("/pbac/policies")
    assert r.status_code == 200
    ids = {p["id"] for p in r.json()}
    assert "deny-after-hours-approval" in ids
    assert "admin-full-access" in ids


def test_approve_unknown_invoice_returns_404():
    token = _token("alice_admin")
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/rbac/invoices/NOPE/approve", headers=headers)
    assert r.status_code == 404

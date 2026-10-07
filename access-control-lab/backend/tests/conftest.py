import pytest

from app.db.seed_data import get_invoice, get_user


@pytest.fixture
def alice_admin():
    return get_user("alice_admin")


@pytest.fixture
def bob_finance():
    return get_user("bob_finance")


@pytest.fixture
def carol_auditor():
    return get_user("carol_auditor")


@pytest.fixture
def dave_marketing():
    return get_user("dave_marketing")


@pytest.fixture
def erin_legal():
    return get_user("erin_legal")


@pytest.fixture
def inv_finance_internal():
    return get_invoice("INV-1007")  # FINANCE, internal, $15,000


@pytest.fixture
def inv_finance_restricted():
    return get_invoice("INV-1006")  # FINANCE, restricted, $120,000


@pytest.fixture
def inv_marketing():
    return get_invoice("INV-1005")  # MARKETING, internal, $30,000

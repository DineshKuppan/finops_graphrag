import pytest
from src.domain.identity import canonical_party_key, canonical_identifier


@pytest.mark.parametrize("name", ["ACME, Inc.", "Acme Inc", "acme", "  Acme   Incorporated ", "Acmé LLC"])
def test_name_variants_resolve_to_one_key(name):
    assert canonical_party_key(name) == "acme"


def test_stacked_legal_suffixes_are_stripped():
    assert canonical_party_key("Globex Pvt. Ltd.") == "globex"


def test_suffix_only_name_is_not_emptied():
    assert canonical_party_key("Company") == "company"


def test_ampersand_and_word_and_match():
    assert canonical_party_key("Smith & Sons") == canonical_party_key("Smith and Sons")


def test_distinct_names_stay_distinct():
    assert canonical_party_key("Acme Holdings") != canonical_party_key("Acme Inc")


def test_identifier_formatting_is_ignored():
    assert canonical_identifier("12-345 6789") == canonical_identifier("123456789")
    assert canonical_identifier("gb29 nwbk 6016") == "GB29NWBK6016"

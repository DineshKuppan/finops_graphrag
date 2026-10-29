import re
import unicodedata

_LEGAL_SUFFIXES = {
    "inc", "incorporated", "llc", "llp", "lp", "ltd", "limited", "corp", "corporation",
    "co", "company", "plc", "gmbh", "ag", "sa", "bv", "nv", "pvt", "private", "pte",
}

def canonical_party_key(name: str) -> str:
    """Collapses cosmetic name variants ("ACME, Inc.", "Acme Inc") onto one key so the
    graph holds a single node per real-world party."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    tokens = re.findall(r"[a-z0-9]+", text.lower().replace("&", " and "))
    while len(tokens) > 1 and tokens[-1] in _LEGAL_SUFFIXES:
        tokens.pop()
    return "_".join(tokens)

def canonical_identifier(value: str) -> str:
    """Normalises tax IDs and bank accounts so formatting differences don't hide a match."""
    return re.sub(r"[^A-Za-z0-9]", "", value).upper()

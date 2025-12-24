# backend/security/pii.py
import re
from typing import Tuple, Dict

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?966|0)?5\d{8}(?!\d)|(?<!\d)\+?\d{10,15}(?!\d)")
IBAN_RE  = re.compile(r"\bSA\d{2}[A-Z0-9]{18}\b", re.IGNORECASE)

# Saudi National ID / Iqama commonly 10 digits starting with 1 or 2
SA_ID_RE = re.compile(r"(?<!\d)([12]\d{9})(?!\d)")

# Optional: card-like sequences (very rough; avoid too aggressive masking)
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)")

def mask_pii(text: str) -> Tuple[str, Dict[str, int]]:
    """
    Returns (masked_text, stats).
    Safe for both Arabic & English.
    """
    if not text:
        return text, {"email": 0, "phone": 0, "iban": 0, "sa_id": 0, "card": 0}

    stats = {"email": 0, "phone": 0, "iban": 0, "sa_id": 0, "card": 0}

    def sub_count(pattern, repl, key):
        nonlocal text
        text, n = pattern.subn(repl, text)
        stats[key] += n

    sub_count(EMAIL_RE, "[EMAIL_REDACTED]", "email")
    sub_count(IBAN_RE,  "[IBAN_REDACTED]", "iban")
    sub_count(SA_ID_RE, "[NATIONAL_ID_REDACTED]", "sa_id")
    sub_count(PHONE_RE, "[PHONE_REDACTED]", "phone")

    # Keep card masking last because it can over-match.
    sub_count(CARD_RE,  "[CARD_REDACTED]", "card")

    return text, stats


def mask_hits_contract(contract_hits: list[dict]) -> tuple[list[dict], dict]:
    """
    Mask PII inside clause_text for contract evidence hits.
    Keeps clause_id intact (important for citations).
    """
    total = {"email": 0, "phone": 0, "iban": 0, "sa_id": 0, "card": 0}
    out = []

    for h in (contract_hits or []):
        h2 = dict(h)
        masked, stats = mask_pii(h2.get("clause_text", ""))
        h2["clause_text"] = masked
        for k in total:
            total[k] += stats.get(k, 0)
        out.append(h2)

    return out, total


def mask_hits_law(law_hits: list[dict]) -> tuple[list[dict], dict]:
    """
    Mask PII inside law evidence text (rare, but safe).
    """
    total = {"email": 0, "phone": 0, "iban": 0, "sa_id": 0, "card": 0}
    out = []

    for h in (law_hits or []):
        h2 = dict(h)
        masked, stats = mask_pii(h2.get("text", ""))
        h2["text"] = masked
        for k in total:
            total[k] += stats.get(k, 0)
        out.append(h2)

    return out, total

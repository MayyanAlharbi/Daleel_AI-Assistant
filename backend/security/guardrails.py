# backend/security/guardrails.py
import re

MAX_QUESTION_CHARS = 1200
MAX_TOPIC_ITEMS = 9
MAX_TOPIC_LEN = 40

INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"you\s+are\s+now\s+system",
    r"developer\s+message",
    r"reveal\s+your\s+prompt",
    r"print\s+the\s+system\s+prompt",
    r"jailbreak",
]

_inj_re = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)

def validate_question(text: str) -> None:
    if not text or not text.strip():
        raise ValueError("Empty question.")
    if len(text) > MAX_QUESTION_CHARS:
        raise ValueError(f"Question too long. Max {MAX_QUESTION_CHARS} chars.")
    if _inj_re.search(text):
        raise ValueError("Potential prompt-injection detected. Please rephrase your question.")

def validate_topics(topics: list[str]) -> None:
    if len(topics) > MAX_TOPIC_ITEMS:
        raise ValueError(f"Too many topics. Max {MAX_TOPIC_ITEMS}.")
    for t in topics:
        if len(t) > MAX_TOPIC_LEN:
            raise ValueError(f"Topic too long: {t[:30]}...")

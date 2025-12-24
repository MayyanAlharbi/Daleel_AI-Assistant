import re
from typing import List, Dict

# ----------------------------
# 1) Clean noisy PDF artifacts
# ----------------------------
NOISE_PATTERNS = [
    r"(?im)^\s*page\s+\d+\s+of\s+\d+\s*$",
    r"(?im)^\s*Downloaded\s+at\s*:\s*.*$",
    r"(?im)^\s*By\s*:\s*.*$",
]

def _clean_text(text: str) -> str:
    text = text.replace("\r", "\n")
    # collapse huge blank blocks
    text = re.sub(r"\n{3,}", "\n\n", text)

    # remove common headers/footers
    for pat in NOISE_PATTERNS:
        text = re.sub(pat, "", text)

    # trim spaces per-line
    text = "\n".join([ln.rstrip() for ln in text.split("\n")])
    # remove too many blank lines again
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# ----------------------------
# 2) Heading detection (AR/EN)
# ----------------------------
AR_ORDINALS = (
    "الأولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|"
    "الحادية عشرة|الثانية عشرة|الثالثة عشرة|الرابعة عشرة|الخامسة عشرة|السادسة عشرة|"
    "السابعة عشرة|الثامنة عشرة|التاسعة عشرة|العشرون"
)

# Matches common clause/article headings:
# - Article 1 / Article (1) / ARTICLE 2
# - المادة 1 / المادة (1) / المادة الأولى / المادة: 3
# - 1. / 1- / 1) / (1) / 1.1 / 2.3
# - Section / Chapter (optional)
CLAUSE_HEAD_RE = re.compile(
    rf"""(?mix)
    ^\s*(
        # English articles/sections/chapters
        (?:ARTICLE|Article)\s*\(?\s*\d+\s*\)?\s*|
        (?:Section|SECTION|Chapter|CHAPTER)\s*\(?\s*\d+\s*\)?\s*|

        # Arabic المادة + number/ordinal
        (?:المادة)\s*(?:\(?\s*\d+\s*\)?|(?:{AR_ORDINALS})|[\d\u0660-\u0669]+)\s*|

        # Numbered headings: 1. / 1) / (1) / 1.1
        (?:\d+\.\d+\s*)|
        (?:\d+\)\s*)|
        (?:\(?\s*\d+\s*\)?[\.\-:]?\s*)|

        # English common contract headings (VERY IMPORTANT)
        (?:EMPLOYMENT\s+CONTRACT)\s*|
        (?:FIRST\s+PARTY|SECOND\s+PARTY|THIRD\s+PARTY)\s*:?|
        (?:EMPLOYER|EMPLOYEE)\s*:?|
        (?:JOB\s+TITLE|POSITION|DUTIES)\s*:?|
        (?:WORK\s+LOCATION|WORKPLACE)\s*:?|
        (?:TERM|DURATION|CONTRACT\s+DURATION|RENEWAL)\s*:?|
        (?:PROBATION|PROBATION\s+PERIOD)\s*:?|
        (?:WAGE|SALARY|BASIC\s+SALARY|ALLOWANCE(?:S)?)\s*:?|
        (?:WORKING\s+HOURS|OVERTIME)\s*:?|
        (?:LEAVE|VACATION|ANNUAL\s+LEAVE|SICK\s+LEAVE)\s*:?|
        (?:TERMINATION|NOTICE\s+PERIOD)\s*:?|
        (?:END\s+OF\s+SERVICE|SEVERANCE)\s*:?|
        (?:CONFIDENTIALITY|NON[-\s]?COMPETE)\s*:?
    )
    (?:[-–:]\s*)?
    """,
    re.UNICODE
)


# ----------------------------
# 3) Chunking helpers
# ----------------------------
SENT_SPLIT_RE = re.compile(r"(?<=[\.\!\?\u061F])\s+|\n+")

def _chunk_text(body: str, max_chunk: int = 700, hard_max: int = 1100) -> List[str]:
    """
    Split long body into retrieval-friendly chunks.
    Strategy:
    - split by sentences / line breaks
    - accumulate until max_chunk
    - if a single piece is too large, hard-split it
    """
    body = body.strip()
    if not body:
        return []

    pieces = [p.strip() for p in SENT_SPLIT_RE.split(body) if p.strip()]
    chunks = []
    cur = ""

    for p in pieces:
        if not cur:
            cur = p
            continue

        # if adding p stays within max_chunk, append
        if len(cur) + 1 + len(p) <= max_chunk:
            cur = cur + " " + p
        else:
            chunks.append(cur.strip())
            cur = p

    if cur:
        chunks.append(cur.strip())

    # hard split any huge chunk
    final = []
    for c in chunks:
        if len(c) <= hard_max:
            final.append(c)
        else:
            # split every hard_max chars (avoid infinite)
            for i in range(0, len(c), hard_max):
                final.append(c[i:i + hard_max].strip())

    return [x for x in final if x]


# ----------------------------
# 4) Main splitter
# ----------------------------
def split_into_clauses(
    text: str,
    max_chunk: int = 1400,
    hard_max: int = 2200,
    min_chunk: int = 200
) -> List[Dict[str, str]]:
    """
    Returns list of {clause_id, clause_text}
    - Detect headings (Article/المادة/numbering)
    - For each section, chunk its body into smaller pieces
    """

    text = _clean_text(text)

    # If no headings found, fallback: paragraphs then chunk them
    if not CLAUSE_HEAD_RE.search(text):
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        out = []
        idx = 1
        for p in paras:
            for chunk in _chunk_text(p, max_chunk=max_chunk, hard_max=hard_max):
                if len(chunk) < min_chunk:
                    # attach small chunk to previous clause instead of dropping it
                    if out:
                        out[-1]["clause_text"] += "\n" + chunk
                    else:
                        # first chunk, keep it
                        out.append({"clause_id": f"P{idx:03d}", "clause_text": chunk})
                        idx += 1
                    continue

                out.append({"clause_id": f"P{idx:03d}", "clause_text": chunk})
                idx += 1
        return out

    # Split while keeping headings
    parts = CLAUSE_HEAD_RE.split(text)
    # parts = [pre, head1, body1, head2, body2, ...]

    clauses: List[Dict[str, str]] = []
    article_idx = 1

    # Handle possible text before first heading
    pre = parts[0].strip()
    if pre:
        for chunk in _chunk_text(pre, max_chunk=max_chunk, hard_max=hard_max):
            if len(chunk) >= min_chunk:
                clauses.append({"clause_id": f"PRE-{article_idx:03d}", "clause_text": chunk})
                article_idx += 1

    for i in range(1, len(parts) - 1, 2):
        head = (parts[i] or "").strip()
        body = (parts[i + 1] or "").strip()
        if not body:
            continue

        # Normalize head -> stable ID like A001
        base_id = f"A{article_idx:03d}"
        article_idx += 1

        # chunk the body
        chunks = _chunk_text(body, max_chunk=max_chunk, hard_max=hard_max)

        if not chunks:
            continue

        # If body is short, keep single clause including head
        if len(chunks) == 1:
            clause_text = f"{head}\n{chunks[0]}".strip()
            if len(clause_text) < min_chunk:
                if clauses:
                    clauses[-1]["clause_text"] += "\n" + clause_text
                else:
                    clauses.append({"clause_id": base_id, "clause_text": clause_text})
            else:
                clauses.append({"clause_id": base_id, "clause_text": clause_text})

        else:
            # multiple chunks: A001-01, A001-02...
            for j, c in enumerate(chunks, start=1):
                clause_text = f"{head}\n{c}".strip()
                if len(clause_text) < min_chunk:
                    if clauses:
                        clauses[-1]["clause_text"] += "\n" + clause_text
                    else:
                        clauses.append({"clause_id": f"{base_id}-{j:02d}", "clause_text": clause_text})
                    continue

                clauses.append({"clause_id": f"{base_id}-{j:02d}", "clause_text": clause_text})


    return clauses

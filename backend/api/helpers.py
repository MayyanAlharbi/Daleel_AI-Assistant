import re
from typing import List

from api.deps import client, rag
from api.constants import SUPPORTED_UI_LANGS
from api.constants import DEFAULT_TOPICS, TOPIC_QUERIES, SUPPORTED_UI_LANGS, SUMMARY_SCHEMA

from rag.engine import detect_lang


# ----------------------------
# Helpers
# ----------------------------


def norm_clause_id(cid: str) -> str:
    cid = str(cid).strip().upper()
    m = re.search(r"(\d+)", cid)
    if not m:
        return cid
    return f"A{int(m.group(1)):03d}"

def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    if not text:
        return text
    if source_lang == target_lang:
        return text

    prompt = (
        f"Translate the following text from {source_lang} to {target_lang}.\n"
        f"Do NOT explain. Return only the translation.\n\n{text}"
    )

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        temperature=0
    )
    return resp.output_text.strip()


def detect_user_lang_llm(text: str) -> str:
    # Fast path: Arabic script => ar
    if detect_lang(text) == "ar":
        return "ar"

    prompt = (
        "Detect the language of this text. "
        "Return ONLY one code from: ar, en, ur, hi, tl.\n\n"
        f"TEXT:\n{text}"
    )
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        temperature=0
    )
    code = resp.output_text.strip().lower()
    return code if code in SUPPORTED_UI_LANGS else "en"


def ui_format_rules(lang: str) -> str:
    # localized labels for citations + headings
    labels = {
        "en": {
            "contract": "Contract",
            "law": "Labor Law",
            "h_contract": "From your contract",
            "h_law": "Saudi Labor Law",
        },
        "ar": {
            "contract": "العقد",
            "law": "نظام العمل",
            "h_contract": "من العقد",
            "h_law": "نظام العمل السعودي",
        },
        "ur": {
            "contract": "معاہدہ",
            "law": "محنت قانون",
            "h_contract": "معاہدے سے",
            "h_law": "سعودی لیبر قانون",
        },
        "hi": {
            "contract": "कॉन्ट्रैक्ट",
            "law": "श्रम कानून",
            "h_contract": "कॉन्ट्रैक्ट से",
            "h_law": "सऊदी श्रम कानून",
        },
        "tl": {
            "contract": "Kontrata",
            "law": "Batas sa Paggawa",
            "h_contract": "Mula sa kontrata",
            "h_law": "Batas sa Paggawa ng Saudi",
        },
    }
    L = labels.get(lang, labels["en"])

    return f"""
You are a contract Q&A assistant for Saudi employment contracts.

RULES:
- Answer ONLY using the provided EVIDENCE snippets.
- Do NOT invent missing details.
- Write the entire answer in this language: {lang}.
- Do NOT mention contract_id anywhere.
- Do NOT write "insufficient evidence" or any similar sentence.

STRICT OUTPUT FORMAT:
1) Start with ONE short direct answer sentence (no citation).
2) Then output:

## {L["h_contract"]}
- Bullet points ONLY from CONTRACT evidence.
- Every bullet MUST end with: ({L["contract"]}: clause_id=<CLAUSE_ID>)

3) Include the LAW section ONLY IF it is clearly relevant to the question AND you will add at least ONE law bullet:

## {L["h_law"]}
- Bullet points ONLY from LAW evidence.
- Every bullet MUST end with: ({L["law"]}: Article=<ARTICLE_NUMBER_OR_TITLE>)

4) Do NOT add any extra headings/sections.
5) Do NOT add placeholders like "(Contract: not found)".
""".strip()



def dedupe_hits(hits):
    seen = set()
    out = []
    for h in hits:
        key = (h.get("contract_id"), h.get("clause_id"))
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out



def build_contract_evidence(
    contract_id: str,
    queries: list[str],
    k_each: int = 4,
    max_total: int = 18,
    wanted_labels: set[str] | None = None,
):
    """
    Retrieve contract clauses evidence for a list of topic queries.
    If wanted_labels is provided, we filter retrieved hits by those labels.

    Expected hit format from rag.retrieve_contract():
      {
        "clause_id": "...",
        "clause_text": "...",
        "score": float,
        # optional: "label": "salary_terms"  (we will attach it if missing)
      }

    Expected meta in rag.store[contract_id]["meta"] list with items like:
      {
        "clause_id": "...",
        "clause_text": "...",
        "language": "...",
        "label": "salary_terms"   # must exist if you integrated classifier at upload
      }
    """

    bundle = rag.store.get(contract_id)
    if not bundle:
        return []

    meta_list = bundle.get("meta", [])


    # Build clause_id -> label map (fast lookup)
    id_to_label = {}
    for m in meta_list:
        cid = m.get("clause_id")
        if cid:
            id_to_label[cid] = m.get("label")
    print("META_LEN:", len(meta_list))
    print("META_SAMPLE_LABELS:", [(m.get("clause_id"), m.get("label")) for m in meta_list[:8]])

    # Collect hits for each query
    all_hits = []
    for q in queries:
        hits = rag.retrieve_contract(contract_id, q, k=k_each) or []
        for h in hits:
            # attach label if missing
            if "label" not in h:
                h["label"] = id_to_label.get(h.get("clause_id"))
            h["_topic_query"] = q  # optional debug/useful grouping
        all_hits.extend(hits)

    # OPTIONAL: filter by wanted labels (focused mode)
    if wanted_labels:
        all_hits = [h for h in all_hits if h.get("label") in wanted_labels]

    # Deduplicate by clause_id keeping highest score
    best_by_id = {}
    for h in all_hits:
        cid = norm_clause_id(h.get("clause_id"))
        h["clause_id"] = cid

        if not cid:
            continue
        prev = best_by_id.get(cid)
        if (prev is None) or (h.get("score", 0) > prev.get("score", 0)):
            best_by_id[cid] = h

    # Sort by similarity score desc and cut to max_total
    merged = sorted(best_by_id.values(), key=lambda x: x.get("score", 0), reverse=True)
    return merged[:max_total]



def build_law_evidence(queries: List[str], lang: str, k_each=3, max_total=10):
    all_hits = []
    for q in queries:
        all_hits.extend(rag.retrieve_law(q, lang=lang, k=k_each))
    seen = set()
    out = []
    for h in sorted(all_hits, key=lambda x: x["score"], reverse=True):
        key = (h.get("article"), h.get("title"))
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
        if len(out) >= max_total:
            break
    return out


def format_contract_hits(contract_hits):
    lines = ["### CONTRACT EVIDENCE"]
    for h in contract_hits:
        lines.append(
            f"[CONTRACT] clause_id={h['clause_id']} | lang={h.get('language')} | score={h['score']:.3f}"
        )
        lines.append(h["clause_text"])
        lines.append("")
    return lines


def format_law_hits(law_hits):
    lines = ["### LABOR LAW EVIDENCE"]
    for h in law_hits:
        lines.append(
            f"[LAW] title={h.get('title')} | article={h.get('article')} | lang={h.get('language')} | score={h['score']:.3f}"
        )
        lines.append(h["text"])
        lines.append("")
    return lines


def is_mixed_lang(text: str) -> bool:
    has_ar = bool(re.search(r"[\u0600-\u06FF]", text))
    has_lat = bool(re.search(r"[A-Za-z]", text))
    return has_ar and has_lat

def merge_hits(*lists, max_total=8):
    seen = set()
    out = []
    for hits in lists:
        for h in hits:
            key = (h.get("contract_id"), h.get("clause_id"))
            if key in seen:
                continue
            seen.add(key)
            out.append(h)
    # sort by score desc if score exists
    out.sort(key=lambda x: x.get("score", 0), reverse=True)
    return out[:max_total]


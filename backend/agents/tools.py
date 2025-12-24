from __future__ import annotations
from typing import List, Dict, Any, Optional
import re
from security.pii import mask_hits_contract, mask_hits_law

from api.deps import rag, client
from rag.engine import detect_lang
from api.helpers import (
    translate_text,   # if you moved it elsewhere adjust import
    ui_format_rules,
    format_contract_hits,
    format_law_hits,
    merge_hits,
    dedupe_hits,
)

def detect_user_lang(question: str) -> str:
    # simple + reliable: Arabic script => ar, else en
    return detect_lang(question)

def decide_pivot(contract_lang: str) -> str:
    # If contract is mixed, we still pivot to en for law by default (your old logic)
    return "en" if contract_lang == "en" else "ar"

def retrieve_evidence(
    contract_id: Optional[str],
    question: str,
    user_lang: str,
    pivot_lang: str,
) -> tuple[list[dict], list[dict]]:
    """
    Returns (contract_hits, law_hits)
    """
    
    contract_hits = []
    if contract_id:
        bundle = rag.store.get(contract_id)
        contract_lang = bundle["meta"][0].get("language", "en") if bundle and bundle.get("meta") else "en"

        # bilingual retrieval for mixed contracts (same idea as your existing /ask)
        q_ar = question if user_lang == "ar" else translate_text(question, source_lang=user_lang, target_lang="ar")
        q_en = question if user_lang == "en" else translate_text(question, source_lang=user_lang, target_lang="en")

        if contract_lang == "mixed":
            hits_ar = rag.retrieve_contract(contract_id, q_ar, k=6) or []
            hits_en = rag.retrieve_contract(contract_id, q_en, k=6) or []
            contract_hits = merge_hits(hits_ar, hits_en, max_total=12)
        else:
            q_pivot = q_en if pivot_lang == "en" else q_ar
            contract_hits = rag.retrieve_contract(contract_id, q_pivot, k=12) or []

        # extra safety: dedupe
        contract_hits = sorted(dedupe_hits(contract_hits), key=lambda x: x.get("score", 0), reverse=True)[:12]


        # ✅ PII MASKING for CONTRACT hits (right here)
        contract_hits, pii_stats_c = mask_hits_contract(contract_hits)

        # law retrieval
        q_law = question if user_lang == pivot_lang else translate_text(
            question, source_lang=user_lang, target_lang=pivot_lang
        )
        law_hits = rag.retrieve_law(q_law, lang=pivot_lang, k=10) or []

        # ✅ PII MASKING for LAW hits (right here)
        law_hits, pii_stats_l = mask_hits_law(law_hits)

        # Optional: log stats for debugging + report evidence
        try:
            total = {k: pii_stats_c.get(k, 0) + pii_stats_l.get(k, 0) for k in pii_stats_l}
            print("[SECURITY] PII masked:", total)
        except Exception:
            pass

    return contract_hits, law_hits
\

def llm_write_answer(
    question: str,
    user_lang: str,
    normalized_question: str,
    contract_hits: list[dict],
    law_hits: list[dict],
) -> str:
    # Build evidence blocks (same as your existing /ask)
    evidence_lines = []
    evidence_lines += format_contract_hits(contract_hits)
    evidence_lines += format_law_hits(law_hits)

    system = ui_format_rules(user_lang)

    has_law = bool(law_hits)
    if not has_law:
        system += "\n\nIMPORTANT: There is NO law evidence provided. Do NOT output the law section."

    user = f"USER QUESTION (normalized for retrieval):\n{normalized_question}\n\n" + "\n".join(evidence_lines)

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=[{"role": "system", "content": system},
               {"role": "user", "content": user}],
        temperature=0.2
    )

    # Remove any forbidden “insufficient evidence” lines (same as your ask cleanup)
    final_answer = (resp.output_text or "").strip()
    cleaned = []
    for ln in final_answer.splitlines():
        if re.search(r"insufficient\s+evidence|evidence\s+is\s+insufficient", ln, re.IGNORECASE):
            continue
        cleaned.append(ln)
    return "\n".join(cleaned).strip()

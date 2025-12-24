from __future__ import annotations

import json
from typing import TypedDict, List, Optional, Dict, Any, Set
from security.pii import mask_hits_contract, mask_hits_law

from langgraph.graph import StateGraph, END

from api.constants import DEFAULT_TOPICS, TOPIC_QUERIES, SUPPORTED_UI_LANGS
from api.schemas import SummaryRequest
from api.deps import rag, client
from api.helpers import (
    build_contract_evidence,
    build_law_evidence,
    format_contract_hits,
    format_law_hits,
)

# UI topic -> classifier label (same as you used)
TOPIC_TO_LABEL = {
    "Salary": "salary_terms",
    "Probation": "probation",
    "Termination": "termination",
    "Working Hours": "working_hours",
    "Leave": "leave",
    "Benefits": "benefits",
    "Penalties": "penalties",
    "Duration": "contract_duration",
    "Non-Compete": "non_compete",
}


class SummaryState(TypedDict, total=False):
    req: SummaryRequest

    user_lang: str
    contract_lang: str
    pivot_lang: str

    queries: List[str]
    topics: List[str]
    wanted_labels: Optional[Set[str]]

    contract_hits_raw: List[Dict[str, Any]]
    contract_hits: List[Dict[str, Any]]
    law_hits: List[Dict[str, Any]]

    evidence_lines: List[str]

    summary_obj: Dict[str, Any]
    error: str


def _safe_lang(code: Optional[str]) -> str:
    code = (code or "en").lower().strip()
    return code if code in SUPPORTED_UI_LANGS else "en"


def _prepare_node(state: SummaryState) -> SummaryState:
    req = state["req"]

    user_lang = _safe_lang(req.language)
    bundle = rag.store.get(req.contract_id)
    contract_lang = bundle["meta"][0].get("language", "en") if bundle and bundle.get("meta") else "en"
    pivot_lang = "en" if contract_lang == "en" else "ar"

    # focused vs full
    if req.mode == "focused":
        topics = req.topics or []
        if not topics:
            return {
                **state,
                "user_lang": user_lang,
                "contract_lang": contract_lang,
                "pivot_lang": pivot_lang,
                "error": "NO_TOPICS",
            }

        queries = [TOPIC_QUERIES.get(t, t) for t in topics]
        wanted_labels = {TOPIC_TO_LABEL.get(t) for t in topics}
        wanted_labels.discard(None)
    else:
        topics = []
        queries = DEFAULT_TOPICS
        wanted_labels = None

    return {
        **state,
        "user_lang": user_lang,
        "contract_lang": contract_lang,
        "pivot_lang": pivot_lang,
        "topics": topics,
        "queries": queries,
        "wanted_labels": wanted_labels,
    }


def _retrieve_node(state: SummaryState) -> SummaryState:
    req = state["req"]
    queries = state.get("queries", [])
    wanted_labels = state.get("wanted_labels", None)

    # 1) Retrieve contract evidence (no filtering here)
    contract_hits_raw = build_contract_evidence(
        req.contract_id,
        queries,
        k_each=4,
        max_total=18,
        wanted_labels=None,   # IMPORTANT: do not filter by label
    ) or []

    # 2) Boost (not filter) if focused + wanted_labels exist
    if wanted_labels:
        for h in contract_hits_raw:
            if h.get("label") in wanted_labels:
                h["score"] = float(h.get("score", 0)) + 0.10
                h["_boosted"] = True
            else:
                h["_boosted"] = False

    contract_hits = sorted(contract_hits_raw, key=lambda x: x.get("score", 0), reverse=True)[:18]
    
    # 3) Law evidence
    pivot_lang = state.get("pivot_lang", "en")
    law_hits = build_law_evidence(queries, lang=pivot_lang, k_each=2, max_total=10) or []

    return {
        **state,
        "contract_hits_raw": contract_hits_raw,
        "contract_hits": contract_hits,
        "law_hits": law_hits,
    }


def _coverage_node(state: SummaryState) -> SummaryState:
    """
    Ensure focused summary doesn't become empty/irrelevant.
    If focused + boosted retrieval still looks weak, we add a fallback retrieval without any boosting.
    """
    req = state["req"]
    wanted_labels = state.get("wanted_labels")
    contract_hits = state.get("contract_hits", [])
    queries = state.get("queries", [])

    if req.mode != "focused":
        return state

    # If too few contract hits, fallback to pure retrieval (still no label filter)
    if len(contract_hits) < 3:
        contract_hits2 = build_contract_evidence(
            req.contract_id,
            queries,
            k_each=6,
            max_total=22,
            wanted_labels=None,
        ) or []
        contract_hits2 = sorted(contract_hits2, key=lambda x: x.get("score", 0), reverse=True)[:18]
        return {**state, "contract_hits": contract_hits2}

    # If we have hits but NONE match wanted_labels, keep them anyway (don’t kill summary)
    # (This is exactly your problem when the classifier is noisy.)
    return state


def _build_evidence_node(state: SummaryState) -> SummaryState:
    
    contract_hits = state.get("contract_hits", []) or []
    law_hits = state.get("law_hits", []) or []

    # ✅ FIX: flatten law_hits if it comes nested (list of lists)
    flat_law_hits = []
    for item in law_hits:
        if isinstance(item, list):
            flat_law_hits.extend(item)
        elif isinstance(item, dict):
            flat_law_hits.append(item)

    law_hits = flat_law_hits

    if not contract_hits and not law_hits:
        return {**state, "error": "NO_EVIDENCE"}

    evidence_lines: List[str] = []
    evidence_lines += format_contract_hits(contract_hits)
    evidence_lines += format_law_hits(law_hits)

    return {**state, "evidence_lines": evidence_lines}



def _generate_node(state: SummaryState) -> SummaryState:
    req = state["req"]
    user_lang = state.get("user_lang", "en")
    evidence_lines = state.get("evidence_lines", [])

    system = f"""
You are generating a CONTRACT SUMMARY (not Q&A).

STRICT RULES:
- Output MUST be valid JSON only (no markdown, no extra text).
- Write ALL text in language: {user_lang}.
- Use ONLY the provided evidence snippets.
- Mode = {req.mode}
- FULL mode: include main sections (salary, probation, working hours, leave, termination, obligations, benefits, penalties, duration, governing law if present).
- FOCUSED mode: include ONLY selected topics.
- Every bullet MUST include at least one source:
  - Contract: {{ "type": "contract", "id": "A015" }}
  - Law: {{ "type": "law", "id": "Article 53" }}

OUTPUT JSON STRUCTURE:
{{
  "mode": "{req.mode}",
  "language": "{user_lang}",
  "overview": [ {{ "text": "...", "sources": [{{"type":"contract","id":"A015"}}] }} ],
  "sections": [
    {{
      "key": "salary",
      "title": "...",
      "bullets": [ {{ "text": "...", "sources": [{{"type":"law","id":"Article 53"}}] }} ]
    }}
  ]
}}
""".strip()

    user = (
        f"MODE: {req.mode}\n"
        f"TOPICS: {req.topics}\n\n"
        + "\n".join(evidence_lines)
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )

    raw = (resp.choices[0].message.content or "").strip()

    # remove code fences if model adds them
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        obj = json.loads(raw)
    except Exception:
        return {**state, "error": "BAD_JSON"}

    return {**state, "summary_obj": obj}


def _finalize_node(state: SummaryState) -> SummaryState:
    # This node exists mainly to keep the graph clean.
    return state


def build_summary_graph():
    g = StateGraph(SummaryState)

    g.add_node("prepare", _prepare_node)
    g.add_node("retrieve", _retrieve_node)
    g.add_node("coverage", _coverage_node)
    g.add_node("build_evidence", _build_evidence_node)
    g.add_node("generate", _generate_node)
    g.add_node("finalize", _finalize_node)

    g.set_entry_point("prepare")

    # If topics missing in focused mode -> stop early
    def route_after_prepare(state: SummaryState):
        return END if state.get("error") == "NO_TOPICS" else "retrieve"

    g.add_conditional_edges("prepare", route_after_prepare, {"retrieve": "retrieve", END: END})

    g.add_edge("retrieve", "coverage")
    g.add_edge("coverage", "build_evidence")

    # If no evidence -> stop early
    def route_after_evidence(state: SummaryState):
        return END if state.get("error") == "NO_EVIDENCE" else "generate"

    g.add_conditional_edges("build_evidence", route_after_evidence, {"generate": "generate", END: END})

    # If JSON parsing fails -> stop early
    def route_after_generate(state: SummaryState):
        return END if state.get("error") else "finalize"

    g.add_conditional_edges("generate", route_after_generate, {"finalize": "finalize", END: END})

    g.add_edge("finalize", END)

    return g.compile()


SUMMARY_GRAPH = build_summary_graph()


def run_summary(req: SummaryRequest) -> dict:
    state: SummaryState = {"req": req}
    out = SUMMARY_GRAPH.invoke(state)

    user_lang = out.get("user_lang", _safe_lang(req.language))
    if out.get("error") == "NO_TOPICS":
        msg_map = {
            "ar": "اختر موضوعًا واحدًا على الأقل للتلخيص المركز.",
            "en": "Please select at least one topic for a focused summary.",
            "ur": "مرکوز خلاصے کے لیے کم از کم ایک موضوع منتخب کریں۔",
            "hi": "फोकस्ड सारांश के लिए कम से कम एक विषय चुनें।",
            "tl": "Pumili ng kahit isang topic para sa focused summary."
        }
        return {"summary": msg_map.get(user_lang, msg_map["en"]), "contract_id": req.contract_id, "language": user_lang}

    if out.get("error") == "NO_EVIDENCE":
        msg_map = {
            "ar": "لم يتم العثور على أدلة كافية للتلخيص.",
            "en": "Not found in the provided contract/law evidence.",
            "ur": "خلاصہ بنانے کے لیے کافی شواہد نہیں ملے۔",
            "hi": "सारांश के लिए पर्याप्त प्रमाण नहीं मिला।",
            "tl": "Walang sapat na ebidensya para gumawa ng summary."
        }
        return {"summary": msg_map.get(user_lang, msg_map["en"]), "contract_id": req.contract_id, "language": user_lang}

    if out.get("error") == "BAD_JSON":
        msg_map = {
            "ar": "تعذر توليد ملخص منظم. حاول مرة أخرى.",
            "en": "Failed to generate a structured summary. Please try again.",
            "ur": "منظم خلاصہ تیار نہیں ہو سکا۔ دوبارہ کوشش کریں۔",
            "hi": "संरचित सारांश नहीं बन पाया। कृपया फिर कोशिश करें।",
            "tl": "Hindi nakagawa ng structured summary. Subukan ulit."
        }
        return {"summary": msg_map.get(user_lang, msg_map["en"]), "contract_id": req.contract_id, "language": user_lang}

    return {"summary": out["summary_obj"], "contract_id": req.contract_id, "language": user_lang}

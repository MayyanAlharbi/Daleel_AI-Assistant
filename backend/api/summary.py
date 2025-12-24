# import json
# from fastapi import APIRouter

# from api.schemas import SummaryRequest
# from api.constants import DEFAULT_TOPICS, TOPIC_QUERIES, SUPPORTED_UI_LANGS
# from api.deps import rag, client
# from api.helpers import (
#     build_contract_evidence,
#     build_law_evidence,
#     format_contract_hits,
#     format_law_hits,
# )

# router = APIRouter(tags=["summary"])

from fastapi import APIRouter, Request
from api.schemas import SummaryRequest
from agents.summary_graph import run_summary

from security.rate_limit import limiter
from security.guardrails import validate_topics
from security.pii import mask_hits_contract, mask_hits_law  # (optional, see notes below)

router = APIRouter(tags=["summary"])

@router.post("/summary")
def summary(req: SummaryRequest, request: Request):
    # 1) Rate limit (summary is heavier than ask)
    ip = request.client.host if request.client else "unknown"
    limiter.check(f"summary:{ip}", limit=15)

    # 2) Validate topics only when focused
    if req.mode == "focused" and req.topics:
        validate_topics(req.topics)

    # 3) Run LangGraph summary
    result = run_summary(req)

    return result

# @router.post("/summary")
# def summary(req: SummaryRequest):
#     # 1) Output language (UI language)
#     user_lang = (req.language or "en").lower().strip()
#     if user_lang not in SUPPORTED_UI_LANGS:
#         user_lang = "en"

#     # 2) Contract language from stored clauses
#     bundle = rag.store.get(req.contract_id)
#     contract_lang = bundle["meta"][0].get("language", "en") if bundle and bundle.get("meta") else "en"

#     # 3) Pivot language for retrieval (match evidence language)
#     pivot_lang = "en" if contract_lang == "en" else "ar"

#     # UI topic -> classifier label
#     TOPIC_TO_LABEL = {
#         "Salary": "salary_terms",
#         "Probation": "probation",
#         "Termination": "termination",
#         "Working Hours": "working_hours",
#         "Leave": "leave",
#         "Benefits": "benefits",
#         "Penalties": "penalties",
#         "Duration": "contract_duration",
#         "Non-Compete": "non_compete",
#     }

#     # 4) Build queries + wanted_labels (focused only)
#     if req.mode == "focused":
#         topics = req.topics or []
#         if not topics:
#             msg_map = {
#                 "ar": "اختر موضوعًا واحدًا على الأقل للتلخيص المركز.",
#                 "en": "Please select at least one topic for a focused summary.",
#                 "ur": "مرکوز خلاصے کے لیے کم از کم ایک موضوع منتخب کریں۔",
#                 "hi": "फोकस्ड सारांश के लिए कम से कम एक विषय चुनें।",
#                 "tl": "Pumili ng kahit isang topic para sa focused summary.",
#             }
#             return {"summary": msg_map.get(user_lang, msg_map["en"]), "contract_id": req.contract_id, "language": user_lang}

#         queries = [TOPIC_QUERIES.get(t, t) for t in topics]

#         wanted_labels = {TOPIC_TO_LABEL.get(t) for t in topics}
#         wanted_labels.discard(None)
#     else:
#         queries = DEFAULT_TOPICS
#         wanted_labels = set()  # IMPORTANT: keep as empty set (no filtering/boost needed)

#     # 5) Retrieve raw contract evidence (NO label filtering here)
#     contract_hits_raw = build_contract_evidence(
#         req.contract_id,
#         queries,
#         k_each=4,
#         max_total=30,         # get more, then we rank/trim
#         wanted_labels=None,   # IMPORTANT: never filter here
#     ) or []

#     # 6) Label-based BOOST (NOT FILTER)
#     if wanted_labels:
#         for h in contract_hits_raw:
#             if h.get("label") in wanted_labels:
#                 h["score"] = float(h.get("score", 0)) + 0.10
#                 h["_boosted"] = True
#             else:
#                 h["_boosted"] = False

#     # 7) Final top-K contract hits
#     contract_hits = sorted(contract_hits_raw, key=lambda x: float(x.get("score", 0)), reverse=True)[:18]

#     # 8) Law evidence (topic-based)
#     law_hits = build_law_evidence(queries, lang=pivot_lang, k_each=2, max_total=10) or []

#     if not contract_hits and not law_hits:
#         msg_map = {
#             "ar": "لم يتم العثور على أدلة كافية للتلخيص.",
#             "en": "Not found in the provided contract/law evidence.",
#             "ur": "خلاصہ بنانے کے لیے کافی شواہد نہیں ملے۔",
#             "hi": "सारांश के लिए पर्याप्त प्रमाण नहीं मिला।",
#             "tl": "Walang sapat na ebidensya para gumawa ng summary.",
#         }
#         return {"summary": msg_map.get(user_lang, msg_map["en"]), "contract_id": req.contract_id, "language": user_lang}

#     evidence_lines = []
#     evidence_lines += format_contract_hits(contract_hits)
#     evidence_lines += format_law_hits(law_hits)

#     # 9) Generate STRICT structured JSON in user_lang (no markdown)
#     system = f"""
# You are generating a CONTRACT SUMMARY (not Q&A).

# STRICT RULES:
# - Output MUST be valid JSON only (no markdown, no extra text).
# - Write ALL text in language: {user_lang}.
# - Use ONLY the provided evidence snippets.
# - Mode = {req.mode}
# - FULL mode: include main sections (salary, probation, working hours, leave, termination, obligations, benefits, penalties, duration, governing law if present).
# - FOCUSED mode: include ONLY selected topics.
# - Every bullet MUST include at least one source:
#   - Contract: {{ "type": "contract", "id": "A015" }}
#   - Law: {{ "type": "law", "id": "Article 53" }}

# OUTPUT JSON STRUCTURE (must match exactly):
# {{
#   "mode": "{req.mode}",
#   "language": "{user_lang}",
#   "overview": [ {{ "text": "...", "sources": [{{"type":"contract","id":"A015"}}] }} ],
#   "sections": [
#     {{
#       "key": "salary",
#       "title": "...",
#       "bullets": [ {{ "text": "...", "sources": [{{"type":"law","id":"Article 53"}}] }} ]
#     }}
#   ]
# }}
# """.strip()

#     user = (
#         f"MODE: {req.mode}\n"
#         f"TOPICS: {req.topics}\n\n"
#         + "\n".join(evidence_lines)
#     )

#     resp = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": system},
#             {"role": "user", "content": user},
#         ],
#         temperature=0.2,
#     )

#     raw = (resp.choices[0].message.content or "").strip()

#     # Remove code fences if model adds them
#     if raw.startswith("```"):
#         raw = raw.replace("```json", "").replace("```", "").strip()

#     try:
#         summary_obj = json.loads(raw)
#     except Exception:
#         msg_map = {
#             "ar": "تعذر توليد ملخص منظم. حاول مرة أخرى.",
#             "en": "Failed to generate a structured summary. Please try again.",
#             "ur": "منظم خلاصہ تیار نہیں ہو سکا۔ دوبارہ کوشش کریں۔",
#             "hi": "संरचित सारांश नहीं बन पाया। कृपया फिर कोशिश करें।",
#             "tl": "Hindi nakagawa ng structured summary. Subukan ulit.",
#         }
#         return {"summary": msg_map.get(user_lang, msg_map["en"]), "contract_id": req.contract_id, "language": user_lang}

#     return {"summary": summary_obj, "contract_id": req.contract_id, "language": user_lang}

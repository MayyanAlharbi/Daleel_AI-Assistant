import re
from fastapi import APIRouter
from api.schemas import AskRequest, GeneralAskRequest
from api.constants import SUPPORTED_UI_LANGS

from fastapi import Request
from security.pii import mask_hits_contract, mask_hits_law
from security.guardrails import validate_question
from security.rate_limit import limiter
from api.deps import rag, client
from api.helpers import (
    translate_text, ui_format_rules, detect_user_lang_llm,
    format_contract_hits, format_law_hits,
    dedupe_hits, merge_hits
)
from rag.engine import detect_lang
router = APIRouter(tags=["ask"])

from agents.graph import ASK_GRAPH

@router.post("/ask")
def ask(req: AskRequest, request: Request):
    ip = request.client.host if request.client else "unknown"
    limiter.check(f"ask:{ip}", limit=30)

    validate_question(req.question)
    
    result = ASK_GRAPH.invoke({
        "contract_id": req.contract_id,
        "question": req.question,
    })
    return {
        "answer": result["final_answer"],
        "contract_id": req.contract_id,
        "language": result["user_lang"],
    }


# @router.post("/ask")
# def ask(req: AskRequest):
#     user_lang = detect_lang(req.question)

#     bundle = rag.store.get(req.contract_id)
#     contract_lang = bundle["meta"][0].get("language", "en") if bundle else "en"

#     # Always build both query versions (AR + EN) when contract is mixed OR user is AR
#     q_ar = req.question if user_lang == "ar" else translate_text(req.question, source_lang=user_lang, target_lang="ar")
#     q_en = req.question if user_lang == "en" else translate_text(req.question, source_lang=user_lang, target_lang="en")

#     # Retrieve contract evidence (bilingual when mixed)
#     if contract_lang == "mixed":
#         hits_ar = rag.retrieve_contract(req.contract_id, q_ar, k=6)
#         hits_en = rag.retrieve_contract(req.contract_id, q_en, k=6)
#         contract_hits = merge_hits(hits_ar, hits_en, max_total=10)
#         pivot_lang = "en"  # for LAW retrieval preference (you can keep en)
#     else:
#         pivot_lang = "en" if contract_lang == "en" else "ar"
#         q_pivot = q_en if pivot_lang == "en" else q_ar
#         contract_hits = rag.retrieve_contract(req.contract_id, q_pivot, k=8)

#     # Law retrieval (use pivot)
#     law_query = q_en if pivot_lang == "en" else q_ar
#     law_hits = rag.retrieve_law(law_query, lang=pivot_lang, k=8)

#     # 4) Normalize question into pivot for retrieval
#     normalized_question = translate_text(req.question, source_lang=user_lang, target_lang=pivot_lang) \
#         if user_lang != pivot_lang else req.question
#     alt_lang = "ar" if pivot_lang == "en" else "en"
#     alt_question = translate_text(
#         normalized_question,
#         source_lang=pivot_lang,
#         target_lang=alt_lang
#     )

#     hits_primary = rag.retrieve_contract(req.contract_id, normalized_question, k=8)
#     hits_alt = rag.retrieve_contract(req.contract_id, alt_question, k=8)

#     contract_hits = dedupe_hits(hits_primary + hits_alt)
#     contract_hits = sorted(contract_hits, key=lambda x: x["score"], reverse=True)[:12]

#     # 5) Retrieve evidence in pivot
#     contract_hits = rag.retrieve_contract(req.contract_id, normalized_question, k=12)
#     law_hits = rag.retrieve_law(normalized_question, lang=pivot_lang, k=8)

#     if not contract_hits and not law_hits:
#         # keep same UI language
#         msg_map = {
#             "ar": "لم يتم العثور على أدلة كافية في العقد/النظام. حاول إعادة صياغة سؤالك.",
#             "en": "No sufficient evidence found in the contract/law. Please rephrase your question.",
#             "ur": "معاہدے/قانون میں کافی شواہد نہیں ملے۔ براہِ کرم سوال دوبارہ لکھیں۔",
#             "hi": "कॉन्ट्रैक्ट/कानून में पर्याप्त प्रमाण नहीं मिला। कृपया प्रश्न दोबारा लिखें।",
#             "tl": "Walang sapat na ebidensya sa kontrata/batas. Pakirephrase ang tanong mo."
#         }
#         return {"answer": msg_map.get(user_lang, msg_map["en"]), "contract_id": req.contract_id, "language": user_lang}
#     # keep law only if we actually have it
#     has_law = bool(law_hits)

#     evidence_lines = []
#     evidence_lines += format_contract_hits(contract_hits)
#     evidence_lines += format_law_hits(law_hits)

#     print("\n==== ASK DEBUG ====")
#     print("Q raw:", req.question)
#     print("Q normalized:", normalized_question)
#     print("user_lang:", user_lang, "contract_lang:", contract_lang, "pivot_lang:", pivot_lang)
#     print("contract_hits:", len(contract_hits))
#     for h in contract_hits[:10]:
#         preview = h["clause_text"][:160].replace("\n", " ")
#         print(f"- {h['clause_id']} score={h['score']:.3f} :: {preview}")

#     print("law_hits:", len(law_hits))


#     # 6) Generate answer directly in user language (stable format, per-bullet citation only)
#     system = ui_format_rules(user_lang)

#     if not has_law:
#         system += "\n\nIMPORTANT: There is NO law evidence provided. Do NOT output the law section."


#     user = f"USER QUESTION (normalized for retrieval):\n{normalized_question}\n\n" + "\n".join(evidence_lines)

#     resp = client.responses.create(
#         model="gpt-4o-mini",
#         input=[{"role": "system", "content": system},
#                {"role": "user", "content": user}],
#         temperature=0.2
#     )

#     final_answer = resp.output_text.strip()
#     lines = final_answer.splitlines()
#     cleaned = []
#     for ln in lines:
#         if re.search(r"insufficient\s+evidence|evidence\s+is\s+insufficient", ln, re.IGNORECASE):
#             continue
#         cleaned.append(ln)
#     final_answer = "\n".join(cleaned).strip()

#     return {
#         "answer": final_answer,
#         "contract_id": req.contract_id,
#         "language": user_lang
#     }


@router.post("/ask_general")
def ask_general(req: GeneralAskRequest):
    # 1) user language (override or LLM)
    user_lang = (req.language or "").lower().strip() if req.language else None
    if not user_lang:
        user_lang = detect_user_lang_llm(req.question)
    if user_lang not in SUPPORTED_UI_LANGS:
        user_lang = "en"

    # 2) retrieval pivot strategy
    primary_pivot = "en"
    fallback_pivot = "ar"

    q_primary = translate_text(req.question, source_lang=user_lang, target_lang=primary_pivot) \
        if user_lang != primary_pivot else req.question

    law_hits = rag.retrieve_law(q_primary, lang="en", k=10)
    used_pivot = "en"
    normalized_question = q_primary

    if not law_hits:
        q_fb = translate_text(req.question, source_lang=user_lang, target_lang=fallback_pivot) \
            if user_lang != fallback_pivot else req.question
        law_hits = rag.retrieve_law(q_fb, lang="ar", k=10)
        used_pivot = "ar"
        normalized_question = q_fb

    if not law_hits:
        msg_map = {
            "ar": "لم يتم العثور على أدلة كافية في نظام العمل. حاول إعادة صياغة سؤالك.",
            "en": "No sufficient evidence found in the Saudi Labor Law. Please rephrase your question.",
            "ur": "محنت قانون میں کافی شواہد نہیں ملے۔ براہِ کرم سوال دوبارہ لکھیں۔",
            "hi": "श्रम कानून में पर्याप्त प्रमाण नहीं मिला। कृपया प्रश्न दोबारा लिखें।",
            "tl": "Walang sapat na ebidensya sa Labor Law. Pakirephrase ang tanong mo."
        }
        return {"answer": msg_map.get(user_lang, msg_map["en"]), "mode": "general", "language": user_lang}

    evidence_lines = format_law_hits(law_hits)

    system = ui_format_rules(user_lang) + "\nThis is GENERAL Q&A (no uploaded contract). Use only LABOR LAW EVIDENCE."
    user = f"USER QUESTION (normalized for retrieval):\n{normalized_question}\n\n" + "\n".join(evidence_lines)

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.2
    )
    # Generate directly in user_lang, no translation needed
    final_answer = resp.output_text.strip()

    return {"answer": final_answer, "mode": "general", "language": user_lang}


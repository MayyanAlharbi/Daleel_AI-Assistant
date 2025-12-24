import uuid
from fastapi import APIRouter, UploadFile, File
from services.parser import extract_text_pdf, extract_text_docx
from services.chunker import split_into_clauses
from rag.engine import detect_lang
from api.deps import rag
from api.helpers import is_mixed_lang
from api.helpers import norm_clause_id

from ml.infer import predict_clause
from rag.engine import detect_lang


router = APIRouter(tags=["upload_contract"])

@router.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)):
    ext = file.filename.lower().split(".")[-1]
    data = await file.read()

    if ext == "pdf":
        text = extract_text_pdf(data)


    elif ext == "docx":
        text = extract_text_docx(data)

    else:
        return {"error": "Only PDF and DOCX are supported."}
    
    print("---- EXTRACT DEBUG ----")
    print("chars:", len(text))
    print("lines:", len(text.splitlines()))
    print("head:\n", text[:700])
    print("tail:\n", text[-700:])
    print("-----------------------")   

    clauses = split_into_clauses(text)

    total_chars = len(text)
    covered_chars = sum(len(c["clause_text"]) for c in clauses)
    print("Total chars:", total_chars)
    print("Covered chars:", covered_chars)
    print("Coverage %:", round(covered_chars / max(total_chars, 1) * 100, 2))
    print("Clauses:", len(clauses))

    print("FIRST CLAUSE:\n", clauses[0]["clause_text"][:800])
    print("\nMIDDLE CLAUSE:\n", clauses[len(clauses)//2]["clause_text"][:800])
    print("\nLAST CLAUSE:\n", clauses[-1]["clause_text"][:800])

    # --- DEBUG: keyword scan ---
    salary_keys = ["الراتب", "الأجر", "أجر", "basic wage", "salary", "wage", "SAR", "ريال", "ر.س"]

    hits = []
    for c in clauses:
        low = c["clause_text"].lower()
        if any(k.lower() in low for k in salary_keys):
            hits.append((c["clause_id"], c["clause_text"][:200]))

    print("SALARY KEYWORD HITS:", len(hits))
    for h in hits[:10]:
        print(" -", h[0], ":", h[1].replace("\n", " "))


    contract_id = "U" + uuid.uuid4().hex[:8].upper()
    lang = "mixed" if is_mixed_lang(text) else detect_lang(text)


    clauses_meta = []
    for c in clauses:
        clause_id = norm_clause_id(c["clause_id"])

        clause_text = c["clause_text"]
        pred_label = predict_clause(clause_text, detect_lang(clause_text))



        clauses_meta.append({
            "contract_id": contract_id,
            "clause_id": clause_id,
            "clause_text": clause_text,
            "language": detect_lang(clause_text),
            "label": pred_label,
        })
    print("=== LABEL COUNTS ===")
    from collections import Counter
    print(Counter([m["label"] for m in clauses_meta]))



    rag.build_contract_index(contract_id, clauses_meta)
    print("=== SAMPLE CLAUSE LABELS ===")
    for m in clauses_meta[:5]:
        print(m["clause_id"], "->", m.get("label"), "|", m["clause_text"][:80])


    return {"contract_id": contract_id, "language": lang, "num_clauses": len(clauses_meta)}



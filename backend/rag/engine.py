import os, json, re
import faiss
from sentence_transformers import SentenceTransformer
from typing import Tuple

# -----------------------------
# Language Utilities
# -----------------------------

SUPPORTED_LANGS = {
    "ar": "Arabic",
    "en": "English",
    "ur": "Urdu",
    "hi": "Hindi",
    "tl": "Filipino"
}

def detect_lang(text: str) -> str:
    """
    Very lightweight language detection.
    Arabic script -> ar
    Otherwise default to en (will be refined via translation step).
    """
    return "ar" if re.search(r"[\u0600-\u06FF]", text) else "en"


# -----------------------------
# Contract Store
# -----------------------------

class ContractStore:
    """
    In-memory store: contract_id -> {index, meta}
    """
    def __init__(self):
        self.contracts = {}

    def put(self, contract_id: str, index, meta):
        self.contracts[contract_id] = {"index": index, "meta": meta}

    def get(self, contract_id: str):
        return self.contracts.get(contract_id)


# -----------------------------
# RAG Engine
# -----------------------------

class RAGEngine:
    def __init__(self, law_index_path: str, law_meta_path: str):
        self.embedder = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        self.law_index = faiss.read_index(law_index_path)
        with open(law_meta_path, "r", encoding="utf-8") as f:
            self.law_meta = json.load(f)

        self.store = ContractStore()

    # -------------------------
    # Contract Indexing
    # -------------------------

    def build_contract_index(self, contract_id: str, clauses_meta: list):
        texts = [c["clause_text"] for c in clauses_meta]
        emb = self.embedder.encode(texts, normalize_embeddings=True)

        index = faiss.IndexFlatIP(emb.shape[1])
        index.add(emb)

        self.store.put(contract_id, index, clauses_meta)

    def get_contract_clauses(self, contract_id: str):
        bundle = self.store.get(contract_id)
        if not bundle:
            return []
        return bundle["meta"]

    # -------------------------
    # Retrieval
    # -------------------------

    def retrieve_contract(self, contract_id: str, query: str, k=5):
        bundle = self.store.get(contract_id)
        if not bundle:
            return []

        q = self.embedder.encode([query], normalize_embeddings=True)
        D, I = bundle["index"].search(q, k)

        hits = []
        for score, idx in zip(D[0], I[0]):
            item = bundle["meta"][int(idx)]
            hits.append({**item, "score": float(score)})
        return hits

    def retrieve_law(self, query: str, lang: str, k=6):
        q = self.embedder.encode([query], normalize_embeddings=True)
        D, I = self.law_index.search(q, 50)

        hits = []
        for score, idx in zip(D[0], I[0]):
            item = self.law_meta[int(idx)]
            if item.get("language") != lang:
                continue
            hits.append({**item, "score": float(score)})
            if len(hits) >= k:
                break
        return hits

    # -------------------------
    # NEW: Multilingual Helpers
    # -------------------------

    def decide_pivot_language(self, contract_lang: str) -> str:
        """
        English first, Arabic fallback.
        """
        return "en" if contract_lang == "en" else "ar"

    def normalize_query(
        self,
        user_query: str,
        user_lang: str,
        pivot_lang: str,
        translate_fn
    ) -> Tuple[str, str]:
        """
        Returns:
        - normalized_query (pivot language)
        - original_user_language
        """
        if user_lang == pivot_lang:
            return user_query, user_lang

        translated = translate_fn(
            text=user_query,
            source_lang=user_lang,
            target_lang=pivot_lang
        )
        return translated, user_lang

    def localize_answer(
        self,
        answer_text: str,
        pivot_lang: str,
        user_lang: str,
        translate_fn
    ) -> str:
        """
        Translate final answer back to user language if needed.
        """
        if pivot_lang == user_lang:
            return answer_text

        return translate_fn(
            text=answer_text,
            source_lang=pivot_lang,
            target_lang=user_lang
        )

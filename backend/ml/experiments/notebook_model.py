from pathlib import Path
import joblib

from rag.engine import detect_lang
from ml.notebook_preprocess import preprocess

_vectorizer = None
_clf = None

def _load():
    global _vectorizer, _clf
    if _vectorizer is not None and _clf is not None:
        return _vectorizer, _clf

    base_dir = Path(__file__).resolve().parents[1]  # backend/
    model_dir = base_dir / "artifacts" / "classifier"

    _vectorizer = joblib.load(model_dir / "tfidf_vectorizer.joblib")
    _clf = joblib.load(model_dir / "logreg_baseline.joblib")

    print("✅ TF-IDF baseline loaded (notebook model)")
    return _vectorizer, _clf

def predict_label_tfidf(clause_text: str) -> str:
    vectorizer, clf = _load()

    lang = detect_lang(clause_text)  # "ar" or "en"
    cleaned = preprocess(clause_text, lang)

    X = vectorizer.transform([cleaned])
    return str(clf.predict(X)[0])

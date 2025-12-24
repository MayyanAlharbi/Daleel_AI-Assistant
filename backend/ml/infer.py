# backend/ml/infer.py

from pathlib import Path
import joblib
from ml.preprocess import preprocess


BASE_DIR = Path(__file__).resolve().parents[1]   # -> C:\Contract-AI\backend
CLASSIFIER_DIR = BASE_DIR / "artifacts" / "classifier"

vectorizer = joblib.load(CLASSIFIER_DIR / "tfidf_vectorizer.joblib")
clf = joblib.load(CLASSIFIER_DIR / "logreg_baseline.joblib")

print("✅ TF-IDF baseline loaded (notebook model)")


def postprocess_label(text: str, label: str) -> str:
    """
    Lightweight rule-based correction for known overlaps.
    This is applied AFTER ML prediction.
    """
    t = text.lower()

    leave_keywords = [
        "leave", "vacation", "annual leave", "sick leave",
        "إجاز", "اجازه", "إجازة"
    ]

    if label == "benefits" and any(k in t for k in leave_keywords):
        return "leave"

    return label


def predict_clause(text: str, lang: str) -> str:
    """
    End-to-end clause classification using:
    preprocessing → TF-IDF → Logistic Regression → postprocessing
    """
    clean_text = preprocess(text, lang)
    X = vectorizer.transform([clean_text])
    raw_label = clf.predict(X)[0]

    final_label = postprocess_label(text, raw_label)
    return final_label

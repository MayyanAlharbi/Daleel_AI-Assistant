from pathlib import Path
import pandas as pd
import joblib

from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

def split_by_contract(df, test_size=0.2, seed=42):
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(gss.split(df, groups=df["contract_id"]))
    return df.iloc[train_idx].copy(), df.iloc[test_idx].copy()

def upsample_train(df_train, target_min=25, seed=42):
    # Upsample each class to at least target_min samples (TRAIN ONLY)
    parts = []
    for label, grp in df_train.groupby("label"):
        if len(grp) >= target_min:
            parts.append(grp)
        else:
            reps = grp.sample(n=target_min, replace=True, random_state=seed)
            parts.append(reps)
    return pd.concat(parts, ignore_index=True)

def main():
    base_dir = Path(__file__).resolve().parents[1]  # backend/
    data_path = base_dir / "data" / "dataset_contract_clean.csv"
    out_dir = base_dir / "artifacts" / "classifier"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    df["clause_text_clean"] = df["clause_text_clean"].astype(str).fillna("")
    df["label"] = df["label"].astype(str).fillna("general")

    train_df, test_df = split_by_contract(df, test_size=0.2, seed=42)

    # Upsample only train
    train_df_bal = upsample_train(train_df, target_min=25, seed=42)

    X_train = train_df_bal["clause_text_clean"].tolist()
    y_train = train_df_bal["label"].tolist()

    X_test = test_df["clause_text_clean"].tolist()
    y_test = test_df["label"].tolist()

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=2
        )),
        ("clf", LogisticRegression(
            max_iter=4000,
            class_weight="balanced"
        ))
    ])

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    print("\n=== Test Classification Report (contract-level split) ===")
    print(classification_report(y_test, preds, digits=3))

    model_path = out_dir / "tfidf_logreg_pipeline.joblib"
    joblib.dump(model, model_path)
    print(f"\n✅ Saved model: {model_path}")

if __name__ == "__main__":
    main()

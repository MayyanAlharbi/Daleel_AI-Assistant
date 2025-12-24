from pathlib import Path
import json
import numpy as np
import pandas as pd

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, f1_score, classification_report
from ml.preprocess import clean_text

import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
    set_seed,
)



MODEL_NAME = "xlm-roberta-base"   # best multilingual baseline
SEED = 42


def split_by_contract(df: pd.DataFrame, test_size=0.2, seed=SEED):
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(gss.split(df, groups=df["contract_id"]))
    return df.iloc[train_idx].copy(), df.iloc[test_idx].copy()


def make_label_maps(labels):
    uniq = sorted(set(labels))
    label2id = {lab: i for i, lab in enumerate(uniq)}
    id2label = {i: lab for lab, i in label2id.items()}
    return label2id, id2label


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, preds)
    f1_macro = f1_score(labels, preds, average="macro", zero_division=0)
    f1_weighted = f1_score(labels, preds, average="weighted", zero_division=0)
    return {"accuracy": acc, "f1_macro": f1_macro, "f1_weighted": f1_weighted}


def main():
    set_seed(SEED)

    base_dir = Path(__file__).resolve().parents[1]  # backend/
    data_path = base_dir / "data" / "dataset_contract.csv"  # <- put your csv here
    out_dir = base_dir / "artifacts" / "transformer_classifier"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)

    needed = {"contract_id", "clause_text", "label"}
    missing = needed - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}. Found: {list(df.columns)}")

    df["clause_text"] = df["clause_text"].astype(str).fillna("")
    df["label"] = df["label"].astype(str).fillna("general")

    # Preprocess text
    df["text"] = df["clause_text"].apply(clean_text)

    # Remove too-short / empty
    df = df[df["text"].str.len() >= 20].copy()

    # Drop duplicates
    df = df.drop_duplicates(subset=["text", "label"])

    train_df, test_df = split_by_contract(df, test_size=0.2, seed=SEED)

    label2id, id2label = make_label_maps(train_df["label"].tolist() + test_df["label"].tolist())

    train_df["label_id"] = train_df["label"].map(label2id)
    test_df["label_id"] = test_df["label"].map(label2id)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize_batch(batch):
        return tokenizer(batch["text"], truncation=True, max_length=256)

    train_ds = Dataset.from_pandas(train_df[["text", "label_id"]].rename(columns={"label_id": "labels"}))
    test_ds = Dataset.from_pandas(test_df[["text", "label_id"]].rename(columns={"label_id": "labels"}))

    train_ds = train_ds.map(tokenize_batch, batched=True)
    test_ds = test_ds.map(tokenize_batch, batched=True)

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(label2id),
        label2id=label2id,
        id2label=id2label,
    )

    # Training args (safe defaults)
    args = TrainingArguments(
        output_dir=str(out_dir / "runs"),
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=20,
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        num_train_epochs=5,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        fp16=torch.cuda.is_available(),   # auto if GPU
        report_to="none",
        seed=SEED,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=test_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    # Final eval + report
    preds = trainer.predict(test_ds)
    y_true = np.array(test_df["label_id"].tolist())
    y_pred = np.argmax(preds.predictions, axis=-1)

    print("\n=== Final Test Report (contract-level split) ===")
    print(classification_report(
        y_true, y_pred,
        target_names=[id2label[i] for i in range(len(id2label))],
        digits=3,
        zero_division=0
    ))

    # Save model + tokenizer + label maps
    model_dir = out_dir / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(str(model_dir))
    tokenizer.save_pretrained(str(model_dir))

    with open(out_dir / "label_maps.json", "w", encoding="utf-8") as f:
        json.dump({"label2id": label2id, "id2label": id2label}, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Saved Transformer model to: {model_dir}")
    print(f"✅ Saved label maps to: {out_dir / 'label_maps.json'}")


if __name__ == "__main__":
    main()

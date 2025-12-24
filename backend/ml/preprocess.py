# backend/ml/preprocess.py

import re

def clean_text(t: str) -> str:
    t = str(t)
    t = t.replace("\u200f"," ").replace("\u200e"," ")
    t = t.replace("\xa0"," ")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def normalize_arabic(text: str) -> str:
    text = re.sub("[إأآا]", "ا", text)
    text = re.sub("ى", "ي", text)
    text = re.sub("ة", "ه", text)
    return text

def preprocess(text: str, lang: str) -> str:
    text = clean_text(text)
    if lang == "ar":
        text = normalize_arabic(text)
    return text

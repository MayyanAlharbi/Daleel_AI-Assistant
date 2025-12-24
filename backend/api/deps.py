import os
from pathlib import Path
import joblib
from dotenv import load_dotenv
from openai import OpenAI

from rag.engine import RAGEngine

load_dotenv()


BASE_DIR = Path(__file__).resolve().parents[2]   # Contract-AI/
ARTIFACTS_DIR = BASE_DIR / "artifacts"
LAW_INDEX_PATH = ARTIFACTS_DIR / "law" / "law.index"
LAW_META_PATH  = ARTIFACTS_DIR / "law" / "law_meta.json"

rag = RAGEngine(str(LAW_INDEX_PATH), str(LAW_META_PATH))


# OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


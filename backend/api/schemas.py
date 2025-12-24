from typing import List, Optional, Literal
from pydantic import BaseModel

class AskRequest(BaseModel):
    contract_id: str
    question: str

class SummaryRequest(BaseModel):
    contract_id: str
    mode: Literal["full", "focused"] = "full"
    topics: Optional[List[str]] = None
    language: Optional[str] = None  # "ar"/"en"/"ur"/"hi"/"tl"

class GeneralAskRequest(BaseModel):
    question: str
    language: Optional[str] = None

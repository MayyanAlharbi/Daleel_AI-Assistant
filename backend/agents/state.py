from __future__ import annotations
from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict, total=False):
    # Input
    contract_id: Optional[str]
    question: str
    user_lang: str              # "ar" / "en" / "ur" / "hi" / "tl"
    pivot_lang: str             # "ar" or "en" for retrieval

    # Evidence
    contract_hits: List[Dict[str, Any]]
    law_hits: List[Dict[str, Any]]

    # Analysis / Plan
    answer_plan: Dict[str, Any]

    # Output
    final_answer: str

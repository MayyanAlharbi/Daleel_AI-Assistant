from __future__ import annotations
from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.tools import (
    detect_user_lang,
    decide_pivot,
    retrieve_evidence,
    llm_write_answer,
)
from api.deps import rag
from api.helpers import translate_text  # same note: import from your helpers

def retriever_node(state: AgentState) -> AgentState:
    contract_id = state.get("contract_id")
    question = state["question"]

    user_lang = state.get("user_lang") or detect_user_lang(question)

    # detect contract lang
    pivot_lang = "en"
    if contract_id:
        bundle = rag.store.get(contract_id)
        contract_lang = bundle["meta"][0].get("language", "en") if bundle and bundle.get("meta") else "en"
        pivot_lang = decide_pivot(contract_lang)
    else:
        pivot_lang = "en"

    contract_hits, law_hits = retrieve_evidence(contract_id, question, user_lang, pivot_lang)

    state["user_lang"] = user_lang
    state["pivot_lang"] = pivot_lang
    state["contract_hits"] = contract_hits
    state["law_hits"] = law_hits
    return state

def analyst_node(state: AgentState) -> AgentState:
    """
    Keep it simple: analyst just decides normalized_question for the writer,
    and whether law is relevant (writer already skips law section if law_hits empty).
    """
    question = state["question"]
    user_lang = state["user_lang"]
    pivot_lang = state["pivot_lang"]

    normalized = question if user_lang == pivot_lang else translate_text(question, source_lang=user_lang, target_lang=pivot_lang)

    state["answer_plan"] = {
        "normalized_question": normalized,
        "has_contract": bool(state.get("contract_id")),
        "has_law": bool(state.get("law_hits")),
    }
    return state

def writer_node(state: AgentState) -> AgentState:
    plan = state.get("answer_plan") or {}
    normalized = plan.get("normalized_question", state["question"])

    final_answer = llm_write_answer(
        question=state["question"],
        user_lang=state["user_lang"],
        normalized_question=normalized,
        contract_hits=state.get("contract_hits", []),
        law_hits=state.get("law_hits", []),
    )

    state["final_answer"] = final_answer
    return state

def build_ask_graph():
    g = StateGraph(AgentState)

    g.add_node("retriever", retriever_node)
    g.add_node("analyst", analyst_node)
    g.add_node("writer", writer_node)

    g.set_entry_point("retriever")
    g.add_edge("retriever", "analyst")
    g.add_edge("analyst", "writer")
    g.add_edge("writer", END)

    return g.compile()

ASK_GRAPH = build_ask_graph()

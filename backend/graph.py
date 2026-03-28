from langgraph.graph import StateGraph, END
from state import FIRState
from agents import *

def get_msg(state):
    return state["messages"][-1]["content"]
    


def intent_node(state):
    return {"intent": intent_agent(get_msg(state))}


# 🔥 UPDATED (context-aware)
def update_node(state):
    msg = get_msg(state)
    fir = state["fir"]
    last_field = state.get("last_question")

    extracted = extractor_agent(msg, last_field)
    merged = merge_json(fir, extracted)

    return {
        "fir": merged,
        "last_question": None  # reset after use
    }


def description_node(state):
    updated_fir = description_agent(state["fir"])
    return {"fir": updated_fir}


def validate_node(state):
    return {"errors": validation_agent(state["fir"])}


# 🔥 UPDATED
def dialogue_node(state):
    question, field = dialogue_agent(state["fir"])

    return {
        "next_question": question,
        "last_question": field
    }


def review_node(state):
    return {"review": review_agent(state["fir"], state["intent"])}


workflow = StateGraph(FIRState)

workflow.add_node("intent", intent_node)
workflow.add_node("update", update_node)
workflow.add_node("description", description_node)
workflow.add_node("validate", validate_node)
workflow.add_node("dialogue", dialogue_node)
workflow.add_node("review", review_node)

workflow.set_entry_point("intent")

workflow.add_edge("intent", "update")
workflow.add_edge("update", "description")
workflow.add_edge("description", "validate")
workflow.add_edge("validate", "dialogue")
workflow.add_edge("dialogue", END)

graph = workflow.compile()

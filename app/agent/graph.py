from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState
from app.agent.planner import planner_node
from app.agent.retrieve import retrieve_node
from app.agent.tools import tools_node
from app.agent.generator import generator_node
from app.agent.critic import critic_node
from app.agent.generator import DISCLAIMER


MAX_RETRIES = 2


def review_route(state: AgentState) -> str:
    if state.get("approved"):
        return "finalize"

    if state.get("retry_count", 0) < MAX_RETRIES:
        return "retry"

    return "finalize"


def retry_node(state: AgentState) -> dict:
    return {
        "retry_count": state.get("retry_count", 0) + 1
    }


def finalize_node(state: AgentState) -> dict:
    if state.get("approved"):
        answer = state.get("draft_answer", "").strip()
    else:
        answer = (
            "The research assistant could not sufficiently validate "
            "the available evidence to provide a reliable answer. "
            "Please consult the original prescribing information "
            "or a qualified healthcare professional."
        )

    return {
        "final_answer": answer + "\n\n" + DISCLAIMER
    }


builder = StateGraph(AgentState)

builder.add_node("planner", planner_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("tools", tools_node)
builder.add_node("generator", generator_node)
builder.add_node("critic", critic_node)
builder.add_node("retry", retry_node)
builder.add_node("finalize", finalize_node)

builder.add_edge(START, "planner")
builder.add_edge("planner", "retrieve")
builder.add_edge("retrieve", "tools")
builder.add_edge("tools", "generator")
builder.add_edge("generator", "critic")

builder.add_conditional_edges(
    "critic",
    review_route,
    {
        "retry": "retry",
        "finalize": "finalize",
    },
)

builder.add_edge("retry", "retrieve")
builder.add_edge("finalize", END)

graph = builder.compile()
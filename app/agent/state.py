from typing import TypedDict, Any


class AgentState(TypedDict, total=False):
    question: str

    plan: list[str]
    search_queries: list[str]
    selected_tools: list[str]

    evidence: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]

    draft_answer: str

    critic_feedback: str
    additional_queries: list[str]
    approved: bool
    retry_count: int

    final_answer: str
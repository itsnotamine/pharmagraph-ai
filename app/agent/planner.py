import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

MODEL = os.getenv("OPENAI_MODEL")


PLANNER_SYSTEM_PROMPT = """
You are the planning component of an agentic pharmaceutical
research assistant.

Your task is to analyze the user's question and produce a
structured research plan.

You have access to a local pharmaceutical document corpus
containing drug labels, contraindications, warnings,
interactions, and medication information.

Do not answer the user's question yet.

Decide:
1. Which research steps are necessary.
2. Which search queries should be executed.
3. Which tools would be useful.

Available tools:

- contraindication_lookup:
  Find contraindications and relevant safety restrictions.

- interaction_analysis:
  Investigate interactions between medications.

- renal_safety_check:
  Investigate renal function restrictions and eGFR thresholds.

- evidence_comparison:
  Compare findings across medications or documents.

Only select tools that are relevant to the question.

Important:
- Never invent clinical facts.
- Never assume a medication is safe.
- Prefer official evidence from the local corpus.
- Produce a plan applicable to any medication question.
- Return ONLY a valid JSON object.

Expected JSON structure:

{
  "plan": [
    "Research step 1",
    "Research step 2"
  ],
  "search_queries": [
    "Search query 1",
    "Search query 2"
  ],
  "selected_tools": [
    "contraindication_lookup"
  ]
}
"""


def planner_node(state: dict) -> dict:
    """
    LangGraph node:
    Analyze the question and create a dynamic research plan.
    """

    question = state["question"]

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": PLANNER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    raw_content = response.choices[0].message.content or ""

    # Some models wrap JSON in Markdown code fences.
    cleaned = raw_content.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    try:
        result = json.loads(cleaned)

        if not isinstance(result, dict):
            raise ValueError("Planner response must be a JSON object")

    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            f"Planner returned invalid JSON: {cleaned[:500]}"
        ) from exc

    allowed_tools = {
        "contraindication_lookup",
        "interaction_analysis",
        "renal_safety_check",
        "evidence_comparison",
    }

    plan = result.get("plan", [])
    queries = result.get("search_queries", [])
    selected = result.get("selected_tools", [])

    if not isinstance(plan, list):
        plan = []

    if not isinstance(queries, list):
        queries = []

    if not isinstance(selected, list):
        selected = []

    queries = [
        query.strip()
        for query in queries
        if isinstance(query, str) and query.strip()
    ]

    selected = [
        tool
        for tool in selected
        if isinstance(tool, str) and tool in allowed_tools
    ]

    if not queries:
        queries = [question]

    return {
        "plan": plan,
        "search_queries": queries[:5],
        "selected_tools": list(dict.fromkeys(selected)),
        "retry_count": 0,
    }
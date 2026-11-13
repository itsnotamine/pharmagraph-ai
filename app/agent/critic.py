import json
import re

from app.agent.planner import client, MODEL


def critic_node(state: dict) -> dict:
    evidence = state.get("evidence", [])
    answer = state.get("draft_answer", "")

    valid_ids = {f"E{item['id']}" for item in evidence}
    cited_ids = set(re.findall(r"\[(E\d+)\]", answer))

    invalid_ids = cited_ids - valid_ids

    evidence_summary = "\n\n".join(
        f"[E{item['id']}] {item['source']} | "
        f"{item['section']}\n{item['text'][:1300]}"
        for item in evidence
    )

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict pharmaceutical evidence reviewer. "
                    "Check factual grounding, completeness, correct citations, "
                    "and whether contraindications are distinguished from warnings. "
                    "Reject unsupported medical claims. "
                    "Return ONLY JSON with keys: "
                    "approved (boolean), feedback (string), "
                    "additional_queries (array of strings)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{state['question']}\n\n"
                    f"Answer:\n{answer}\n\n"
                    f"Evidence:\n{evidence_summary}\n\n"
                    f"Invalid citation IDs: {sorted(invalid_ids)}"
                ),
            },
        ],
    )

    raw = response.choices[0].message.content or "{}"
    cleaned = raw.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    try:
        review = json.loads(cleaned)
    except json.JSONDecodeError:
        review = {
            "approved": False,
            "feedback": "Critic returned invalid JSON.",
            "additional_queries": [],
        }

    approved = (
        review.get("approved") is True
        and not invalid_ids
        and bool(cited_ids)
    )

    additional_queries = review.get("additional_queries", [])

    if not isinstance(additional_queries, list):
        additional_queries = []

    return {
        "approved": approved,
        "critic_feedback": str(review.get("feedback", "")),
        "additional_queries": [
            q for q in additional_queries
            if isinstance(q, str) and q.strip()
        ][:3],
    }
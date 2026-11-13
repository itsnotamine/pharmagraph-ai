from pathlib import Path
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.agent.graph import graph
from app.agent.retrieve import get_retriever


app = FastAPI(
    title="PharmaGraph AI",
    description="Agentic Pharmaceutical Research Assistant",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "PharmaGraph AI",
    }


@app.post("/ask")
def ask(payload: AskRequest):
    try:
        result = graph.invoke(
            {
                "question": payload.question,
                "retry_count": 0,
                "additional_queries": [],
                "evidence": [],
            }
        )

        cited_ids = set(
            re.findall(
                r"\[(E\d+)\]",
                result.get("final_answer", "")
            )
        )

        sources = [
            {
                "id": f"E{item['id']}",
                "source": item["source"],
                "section": item["section"],
                "excerpt": item["text"][:500],
            }
            for item in result.get("evidence", [])
            if f"E{item['id']}" in cited_ids
        ]

        return {
            "question": payload.question,
            "answer": result.get("final_answer", ""),
            "sources": sources,
            "agent_trace": {
                "plan": result.get("plan", []),
                "search_queries": result.get("search_queries", []),
                "tools_executed": [
                    item["tool"]
                    for item in result.get("tool_results", [])
                ],
                "critic_approved": result.get("approved", False),
                "critic_feedback": result.get("critic_feedback", ""),
                "retries": result.get("retry_count", 0),
            },
            "disclaimer": (
                "This information is for research and educational "
                "purposes only and is not medical advice."
            ),
        }

    except Exception as exc:
        # Log the technical error server-side, not in the API response.
        import logging
        logging.exception("Agent execution failed")

        raise HTTPException(
            status_code=500,
            detail="The research agent could not complete the request.",
        ) from exc

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def frontend():
    return FileResponse(STATIC_DIR / "index.html")

import secrets
from pathlib import Path
import re
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

from app.auth import ADMIN_EMAIL, verify_password, require_admin

from contextlib import asynccontextmanager
from app.database import (
    init_database,
    create_conversation,
    get_conversation,
    add_message,
)
from app.conversations import router as conversations_router

from app.agent.graph import graph
from app.agent.retrieve import get_retriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(
    title="PharmaGraph AI",
    description="Agentic Pharmaceutical Research Assistant",
    version="1.0.0",
    lifespan=lifespan,
)



app.include_router(conversations_router)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET") or secrets.token_urlsafe(48),
    session_cookie="pharmagraph_session",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=os.getenv("SESSION_HTTPS_ONLY", "false").lower() == "true",
)


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/login")
def login(payload: LoginRequest, request: Request):
    import hmac

    valid_email = hmac.compare_digest(
        payload.email.strip().lower(),
        ADMIN_EMAIL,
    )

    valid_password = verify_password(payload.password)

    if not (valid_email and valid_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    request.session.clear()
    request.session["user"] = ADMIN_EMAIL

    return {
        "authenticated": True,
        "role": "admin",
    }


@app.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"authenticated": False}


@app.get("/auth/me")
def current_user(user: str = Depends(require_admin)):
    return {
        "email": user,
        "role": "admin",
    }


@app.get("/login")
def login_page(request: Request):
    if request.session.get("user") == ADMIN_EMAIL:
        return RedirectResponse("/", status_code=303)

    return FileResponse(STATIC_DIR / "login.html")


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    conversation_id: str | None = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "PharmaGraph AI",
    }


@app.post("/ask")
def ask(payload: AskRequest, request: Request):
    user = request.session.get("user")

    if payload.conversation_id:
        if user != ADMIN_EMAIL:
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
            )

        conversation = get_conversation(user, payload.conversation_id)

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        conversation_id = payload.conversation_id

    elif user == ADMIN_EMAIL:
        conversation_id = create_conversation(user)

    else:
        conversation_id = None

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

        response_data = {
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

        if conversation_id is not None:
            add_message(
                user_email=user,
                conversation_id=conversation_id,
                role="user",
                content=payload.question,
            )

            add_message(
                user_email=user,
                conversation_id=conversation_id,
                role="assistant",
                content=response_data["answer"],
                metadata={
                    "sources": response_data["sources"],
                    "trace": response_data["agent_trace"],
                    "disclaimer": response_data["disclaimer"],
                },
            )

        response_data["conversation_id"] = conversation_id
        return response_data

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
def frontend(request: Request):
    if request.session.get("user") != ADMIN_EMAIL:
        return RedirectResponse("/login", status_code=303)

    return FileResponse(STATIC_DIR / "index.html")

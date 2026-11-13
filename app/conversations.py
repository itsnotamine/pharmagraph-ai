from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth import require_admin
from app.database import (
    create_conversation,
    list_conversations,
    get_conversation,
    add_message,
    delete_conversation,
)

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


class ConversationCreate(BaseModel):
    title: str = Field(
        default="New conversation",
        min_length=1,
        max_length=150,
    )


@router.get("")
def get_conversations(user: str = Depends(require_admin)):
    return {"conversations": list_conversations(user)}


@router.post("")
def new_conversation(
    payload: ConversationCreate,
    user: str = Depends(require_admin),
):
    conversation_id = create_conversation(
        user_email=user,
        title=payload.title,
    )

    return {"id": conversation_id, "title": payload.title}


@router.get("/{conversation_id}")
def conversation_details(
    conversation_id: str,
    user: str = Depends(require_admin),
):
    conversation = get_conversation(user, conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation


@router.delete("/{conversation_id}")
def remove_conversation(
    conversation_id: str,
    user: str = Depends(require_admin),
):
    deleted = delete_conversation(user, conversation_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return {"deleted": True}

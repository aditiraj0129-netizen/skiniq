from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.agents.chat_agent import ask_skincare_chatbot

router = APIRouter()


class ChatIn(BaseModel):
    message: str
    history: Optional[list[dict]] = None   # [{role: "user"/"assistant", content: "..."}]


@router.post("/ask")
def chat(payload: ChatIn):
    result = ask_skincare_chatbot(payload.message, payload.history)
    return result
from fastapi import APIRouter
from .service import get_conversation_service

router = APIRouter(prefix="/conversation", tags=["Conversation Engine"])

@router.get("/")
def get_conversation():
    return get_conversation_service()

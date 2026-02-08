from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from entities.database import get_db
from .service import get_conversation_response
from .schemas import ConversationRequest, ConversationResponse

router = APIRouter(prefix="/conversation", tags=["Conversation Engine"])

@router.post("/", response_model=ConversationResponse)
def conversation_endpoint(request: ConversationRequest, db: Session = Depends(get_db)):
    return get_conversation_response(db, request)

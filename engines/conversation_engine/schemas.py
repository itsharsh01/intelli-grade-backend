from pydantic import BaseModel, UUID4, Field
from typing import List, Optional
from engines.evaluation_engine.schemas import EvaluationResponse

class ConversationRequest(BaseModel):
    user_id: int
    module_context_id: UUID4
    user_question: str
    # Context of the previous question if the user is answering a cross-question
    context_question: Optional[str] = None

class ConversationResponse(BaseModel):
    response: str
    evaluation: Optional[EvaluationResponse] = None
    follow_up_questions: List[str] = []

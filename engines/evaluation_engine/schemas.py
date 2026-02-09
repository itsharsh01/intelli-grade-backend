from pydantic import BaseModel, Field, UUID4
from typing import List, Optional, Dict, Any

class EvaluationRequest(BaseModel):
    user_id: int
    module_content_id: Optional[UUID4] = None
    module_context: Optional[Dict[str, Any]] = None
    question_context: Optional[Dict[str, Any]] = None
    user_answer: str

class EvaluationResponse(BaseModel):
    correctness: float = Field(..., ge=0.0, le=1.0)
    conceptual_depth: float = Field(..., ge=0.0, le=1.0)
    reasoning_quality: float = Field(..., ge=0.0, le=1.0)
    confidence_alignment: float = Field(..., ge=0.0, le=1.0)
    misconceptions: List[str]
    feedback: str

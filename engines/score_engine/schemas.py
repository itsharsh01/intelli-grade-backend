from pydantic import BaseModel, UUID4, Field, ConfigDict
from typing import List, Optional, Dict

class ScoreCreate(BaseModel):
    user_id: int
    module_content_id: Optional[UUID4]
    score_type: str
    weight: float = 1.0
    correctness: float
    conceptual_depth: float
    reasoning_quality: float
    confidence_alignment: float
    misconceptions: List[str] = []
    feedback: Optional[str] = ""

class ScoreResponse(ScoreCreate):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)

class ModuleScoreSummary(BaseModel):
    module_content_id: UUID4
    
    # Aggregated Scores
    total_score: float = 0.0 # 0.0 - 1.0
    color_grade: str # 'yellow', 'blue', 'orange', 'red'
    
    # Components
    question_completion_score: float = 0.5 # Static value as requested
    evaluation_score: float = 0.0 # Mean of evaluation_engine scores
    conversation_score: float = 0.0 # Mean of conversation scores
    
    # Details
    evaluation_count: int = 0
    conversation_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class CourseScoreSummary(BaseModel):
    course_id: UUID4
    course_name: str
    
    # Aggregated Scores
    total_score: float = 0.0
    color_grade: str
    
    question_completion_score: float = 0.5
    evaluation_score: float = 0.0
    conversation_score: float = 0.0
    
    evaluation_count: int = 0
    conversation_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

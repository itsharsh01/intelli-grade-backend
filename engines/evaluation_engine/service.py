import json
from sqlalchemy.orm import Session
from core.genai_service import genai_service
from .schemas import EvaluationRequest, EvaluationResponse
from engines.score_engine.service import create_score
from engines.score_engine.schemas import ScoreCreate

def evaluate_answer(db: Session, request: EvaluationRequest) -> EvaluationResponse:
    prompt = f"""
    You are an expert educational evaluator. Your task is to evaluate a student's answer to a quiz question based on the provided context.
    
    You must return the evaluation in strict JSON format. Do not include any markdown formatting (like ```json), just the raw JSON object.

    Input Data:
    - Module Context: {json.dumps(request.module_context) if request.module_context else "None"}
    - Question Context: {json.dumps(request.question_context) if request.question_context else "None"}
    - User Answer: {request.user_answer}

    Evaluation Criteria:
    1. Correctness (0.0 - 1.0): How factually correct is the answer?
    2. Conceptual Depth (0.0 - 1.0): Does the answer demonstrate deep understanding or just surface-level recall?
    3. Reasoning Quality (0.0 - 1.0): is the logic sound?
    4. Confidence Alignment (0.0 - 1.0): Does the answer style match the expected confidence for this difficulty?
    5. Misconceptions: List any specific misunderstandings identified.
    6. Feedback: A short, neutral, constructive comment.

    Required Output JSON Format:
    {{
      "correctness": float,
      "conceptual_depth": float,
      "reasoning_quality": float,
      "confidence_alignment": float,
      "misconceptions": [list of strings],
      "feedback": "string"
    }}
    """

    try:
        response_text = genai_service.generate_response(prompt, config={"response_mime_type": "application/json"})
        response_data = json.loads(response_text)
        
        evaluation = EvaluationResponse(
            correctness=response_data.get("correctness", 0.0),
            conceptual_depth=response_data.get("conceptual_depth", 0.0),
            reasoning_quality=response_data.get("reasoning_quality", 0.0),
            confidence_alignment=response_data.get("confidence_alignment", 0.0),
            misconceptions=response_data.get("misconceptions", []),
            feedback=response_data.get("feedback", "")
        )
        
        # Save score
        score_data = ScoreCreate(
            user_id=request.user_id,
            module_content_id=request.module_content_id,
            score_type="evaluation_engine",
            weight=1.0,
            correctness=evaluation.correctness,
            conceptual_depth=evaluation.conceptual_depth,
            reasoning_quality=evaluation.reasoning_quality,
            confidence_alignment=evaluation.confidence_alignment,
            misconceptions=evaluation.misconceptions,
            feedback=evaluation.feedback
        )
        create_score(db, score_data)
        
        return evaluation
    except Exception as e:
        raise ValueError(f"Evaluation failed: {str(e)}")

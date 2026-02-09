from sqlalchemy.orm import Session
from uuid import UUID
from fastapi import HTTPException
from entities.models import ModuleContent
from core.genai_service import genai_service
from .schemas import ConversationRequest, ConversationResponse
from engines.evaluation_engine.schemas import EvaluationResponse
from engines.score_engine.service import create_score
from engines.score_engine.schemas import ScoreCreate
import json

def get_conversation_response(db: Session, request: ConversationRequest) -> ConversationResponse:
    # Fetch module content from DB
    module_content = db.query(ModuleContent).filter(ModuleContent.id == request.module_context_id).first()
    
    if not module_content:
        raise HTTPException(status_code=404, detail="Module content not found")
        
    context_text = module_content.content or ""
    
    # Construct prompt based on whether it's a new question or an answer to a cross-question
    is_answer = request.context_question is not None
    
    if is_answer:
        # User is answering a cross-question
        prompt = (
            f"Context/Topic: {context_text}\n\n"
            f"Question User is Answering: {request.context_question}\n"
            f"User's Answer: {request.user_question}\n\n"
            "Task:\n"
            "1. Evaluate the user's answer for correctness, conceptual depth, reasoning quality, and confidence alignment based on the topic context.\n"
            "2. Provide a simple and concise feedback/explanation.\n"
            "3. Generate 2-3 new follow-up questions to further probe the user's understanding.\n"
            "\n"
            "Output Format (JSON):\n"
            "{\n"
            "  \"response\": \"Your feedback and explanation here.\",\n"
            "  \"evaluation\": {\n"
            "    \"correctness\": <float 0.0-1.0>,\n"
            "    \"conceptual_depth\": <float 0.0-1.0>,\n"
            "    \"reasoning_quality\": <float 0.0-1.0>,\n"
            "    \"confidence_alignment\": <float 0.0-1.0>,\n"
            "    \"misconceptions\": [\"misconception1\", ...],\n"
            "    \"feedback\": \"Same as response or specific feedback string\"\n"
            "  },\n"
            "  \"follow_up_questions\": [\"Q1\", \"Q2\", \"Q3\"]\n"
            "}"
        )
    else:
        # User is asking a new question
        prompt = (
            f"Context/Topic: {context_text}\n\n"
            f"User Question: {request.user_question}\n\n"
            "Task:\n"
            "1. Answer the user's question with a simple and concise explanation.\n"
            "2. Evaluate the DEPTH of the user's question. If it is a basic factual question (e.g., 'What is X?'), DO NOT generate an understanding score (set evaluation to null). If it shows deeper thinking (e.g., 'Why X instead of Y?'), generate an evaluation score for their implied understanding.\n"
            "3. Generate 2-3 follow-up questions to probe their understanding.\n"
            "\n"
            "Output Format (JSON):\n"
            "{\n"
            "  \"response\": \"Your explanation here.\",\n"
            "  \"evaluation\": null OR {\n"
            "    \"correctness\": 1.0,\n" # Assuming question implies correct premise, or evaluate premise
            "    \"conceptual_depth\": <float 0.0-1.0>,\n"
            "    \"reasoning_quality\": <float 0.0-1.0>,\n"
            "    \"confidence_alignment\": 1.0,\n"
            "    \"misconceptions\": [],\n"
            "    \"feedback\": \"Assessment of the question depth\"\n"
            "  },\n"
            "  \"follow_up_questions\": [\"Q1\", \"Q2\", \"Q3\"]\n"
            "}"
        )
    
    # Call Gemini with JSON config
    try:
        response_text = genai_service.generate_response(
            prompt, 
            config={"response_mime_type": "application/json"}
        )
        
        # Parse JSON
        response_data = json.loads(response_text)
        
        evaluation = None
        if response_data.get("evaluation"):
            evaluation = EvaluationResponse(**response_data["evaluation"])
            
            # Save score to DB
            score_data = ScoreCreate(
                user_id=request.user_id,
                module_content_id=request.module_context_id,
                score_type="conversation_evaluation" if is_answer else "question_depth",
                weight=0.5 if is_answer else 0.2,
                correctness=evaluation.correctness,
                conceptual_depth=evaluation.conceptual_depth,
                reasoning_quality=evaluation.reasoning_quality,
                confidence_alignment=evaluation.confidence_alignment,
                misconceptions=evaluation.misconceptions,
                feedback=evaluation.feedback
            )
            create_score(db, score_data)
            
        return ConversationResponse(
            response=response_data.get("response", ""),
            evaluation=evaluation,
            follow_up_questions=response_data.get("follow_up_questions", [])
        )
    except Exception as e:
        # Fallback in case of JSON parse error or API error
        print(f"Error in conversation service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

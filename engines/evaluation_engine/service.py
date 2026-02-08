import json
from core.genai_service import genai_service
from .schemas import EvaluationRequest, EvaluationResponse

def evaluate_answer(request: EvaluationRequest) -> EvaluationResponse:
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
        response_text = genai_service.generate_response(prompt)
        # Attempt to clean potential markdown if the model disobeys
        cleaned_response = response_text.strip().replace("```json", "").replace("```", "")
        response_data = json.loads(cleaned_response)
        return EvaluationResponse(**response_data)
    except json.JSONDecodeError:
        # Fallback or error handling - for now, we'll raise or return a default logic error
        # In a real app, maybe retry or return specific error structure
        raise ValueError(f"LLM returned invalid JSON: {response_text}")
    except Exception as e:
        raise ValueError(f"Evaluation failed: {str(e)}")

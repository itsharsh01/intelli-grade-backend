from core.genai_service import genai_service

def get_conversation_service():
    response = genai_service.generate_response("Hello from the conversation engine! briefly introduce yourself.")
    return {"message": "Conversation Engine Service Response", "ai_response": response}

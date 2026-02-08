from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

class GenAIService:
    _instance = None
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        self.client = genai.Client(api_key=self.api_key)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def generate_response(self, prompt: str, model: str = "gemini-3-flash-preview"):
        """
        Generates content using the specified model.
        
        Args:
            prompt (str): The input prompt for the model.
            model (str): The model to use (default: gemini-3-flash-preview).
            
        Returns:
            str: The generated text response.
        """
        try:
            response = self.client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            # Log the error properly in a real app
            print(f"Error generating content: {e}")
            raise e

# Create a singleton instance for easy import
genai_service = GenAIService.get_instance()

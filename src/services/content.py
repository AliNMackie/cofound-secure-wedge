from typing import List, Dict, Literal
from pydantic import BaseModel
import structlog
import google.generativeai as genai
from src.core.config import settings

logger = structlog.get_logger()

class SectionContent(BaseModel):
    title: str
    content: str
    key_points: List[str]

class ContentGenerator:
    DOMAIN_PROFILES = {
        'consulting': {
            'tone': 'Professional, authoritative, and data-driven. Focus on strategic value, ROI, and scalability.',
            'forbidden_phrases': ['maybe', 'perhaps', 'sort of', 'cool', 'stuff']
        },
        'tech': {
            'tone': 'Technical, precise, and innovative. Focus on architecture, stack details, and performance.',
            'forbidden_phrases': ['magic', 'black box', 'shiny', 'easy', 'guaranteed']
        },
        'finance': {
            'tone': 'Formal, conservative, and risk-aware. Focus on compliance, auditing, and financial stability.',
            'forbidden_phrases': ['crypto', 'moon', 'bet', 'gamble', 'hacker']
        }
    }

    def __init__(self):
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash') # Using a capable model
        else:
            logger.warning("GOOGLE_API_KEY not set. Content generation will fail if called.")
            self.model = None

    def generate_section(self, prompt: str, profile_key: Literal['consulting', 'tech', 'finance']) -> SectionContent:
        """
        Generates a section of content based on the prompt and domain profile.
        """
        if not self.model:
            raise ValueError("Google API Key not configured")

        profile = self.DOMAIN_PROFILES.get(profile_key)
        if not profile:
            raise ValueError(f"Invalid profile key: {profile_key}")

        system_instruction = f"""
        You are an expert content generator acting in a {profile_key} context.
        Tone: {profile['tone']}
        Forbidden Phrases (do not use): {', '.join(profile['forbidden_phrases'])}
        
        Generate a section based on the user's prompt. 
        Return strictly valid JSON matching this schema:
        {{
            "title": "Section Title",
            "content": "The main paragraph text...",
            "key_points": ["Point 1", "Point 2", "Point 3"]
        }}
        """

        full_prompt = f"{system_instruction}\n\nUser Prompt: {prompt}"

        try:
            logger.info("Generating content", profile=profile_key)
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            # Parse and validate using Pydantic
            # validation_model is SectionContent
            # response.text should be the JSON string
            
            section = SectionContent.model_validate_json(response.text)
            return section

        except Exception as e:
            logger.error("Content generation failed", error=str(e))
            raise e

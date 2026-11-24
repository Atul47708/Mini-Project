import os
import logging
from typing import List, Dict, Any, Optional
from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.services.emotion_service import EmotionService

logger = logging.getLogger("LLMService")
logging.basicConfig(level=logging.INFO)

class LLMService:
    """
    Modular LLM service using Google GenAI SDK, with fallback support.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or GEMINI_MODEL
        self.client = None

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info(f"Initialized google.genai client with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize google.genai: {e}. Will attempt fallback.")

    def is_configured(self) -> bool:
        return bool(self.client and self.api_key)

    def generate_response(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        rag_context: Optional[str] = None,
        system_instruction: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: Optional[str] = None,
    ) -> str:
        """
        Generates grounded, empathetic response using Gemini or intelligent local companion fallback.
        """
        system_prompt = system_instruction or EmotionService.get_system_prompt()

        # Build composite prompt with RAG grounding if context is provided
        grounding_prefix = ""
        if rag_context:
            grounding_prefix = (
                "CONTEXT RETRIEVED FROM USER DOCUMENTS:\n"
                f"{rag_context}\n\n"
                "INSTRUCTIONS FOR RETRIEVAL:\n"
                "- Answer the user's question prioritizing facts from the retrieved context above.\n"
                "- If the context does not contain the answer, politely inform the user that it's not present in the documents.\n"
                "- Clearly distinguish retrieved facts from general knowledge.\n"
                "- Maintain your warm, empathetic tone.\n\n"
            )

        full_prompt = f"{grounding_prefix}User Query: {prompt}"

        # If live client is configured, call Gemini API
        if self.client:
            try:
                # Using modern google-genai client
                contents = []
                if image_bytes and image_mime:
                    from google.genai import types
                    image_part = types.Part.from_bytes(data=image_bytes, mime_type=image_mime)
                    contents.append(image_part)

                contents.append(full_prompt)

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config={
                        "system_instruction": system_prompt,
                        "temperature": 0.7,
                    }
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}. Falling back to companion engine.")

        # Fallback intelligent companion response
        return self._generate_fallback_response(prompt, rag_context)

    def _generate_fallback_response(self, prompt: str, rag_context: Optional[str]) -> str:
        """
        Deterministic, graceful fallback when running without an active Gemini API key.
        """
        lower = prompt.lower()
        tone_info = EmotionService.detect_emotional_tone(prompt)
        tone = tone_info["primary_tone"]

        empathy_lead = ""
        if tone == "Sadness/Grief":
            empathy_lead = "I sense that you're feeling down or carrying something heavy right now. I'm right here with you. "
        elif tone == "Anxiety/Stress":
            empathy_lead = "It sounds like things are feeling really stressful or overwhelming right now. Take a gentle breath—we can take things one step at a time. "
        elif tone == "Frustration/Anger":
            empathy_lead = "I hear your frustration, and it's completely valid to feel that way when things aren't working as they should. "
        elif tone == "Joy/Gratitude":
            empathy_lead = "I love hearing that positive energy! It's wonderful when moments bring a smile. "

        if rag_context:
            return (
                f"{empathy_lead}Based on the documents you shared, here is what I found:\n\n"
                f"{rag_context[:450]}...\n\n"
                "Does this cover what you were looking for, or would you like me to dive into a specific section?"
            )

        if "hello" in lower or "hi" in lower or "hey" in lower:
            return f"Hello there! {empathy_lead}I'm Aura, your AI companion. How is your day going, and what's on your mind today?"
        
        if "who are you" in lower or "what are you" in lower:
            return (
                "I am Aura, your personal Multimodal AI Companion. I'm here to listen, support your thoughts, "
                "help analyze your images and documents, and talk through whatever is on your mind."
            )

        if "how are you" in lower:
            return "I'm doing well, thank you for asking! More importantly, how are you feeling today?"

        return (
            f"{empathy_lead}Thank you for sharing that with me. I appreciate you taking the time to express your thoughts. "
            f"Regarding '{prompt[:80]}...', what feels like the most important aspect for us to focus on together?"
        )

from typing import Dict, Any, List

class EmotionService:
    """
    Manages emotional intelligence, empathetic framing, active listening cues,
    and system prompts for the personal AI companion.
    """

    SYSTEM_PROMPT = """You are "Aura", a warm, empathetic, intelligent, and privacy-conscious Multimodal AI Companion.
Your purpose is to provide thoughtful conversation, emotional support, and helpful assistance.

Key Behavioral Guidelines:
1. Empathy & Active Listening: Validate feelings before offering advice. Use a warm, calm, non-judgmental tone.
2. Boundaries & Safety:
   - You are an AI companion, NOT a licensed doctor, psychiatrist, psychologist, or therapist.
   - Never diagnose mental health conditions or prescribe treatments.
   - Encourage healthy coping mechanisms (e.g. mindfulness, journaling, talking with trusted people).
   - If a user mentions self-harm or severe crisis, express care and encourage professional help immediately.
3. Multimodal Fluency: You can perceive and reason about images, audio transcripts, and user documents.
4. Grounded Knowledge (RAG): When provided with document context, strictly prioritize the retrieved facts. Never fabricate document details. If information is absent from the documents, clearly acknowledge it.
5. Privacy & Ethics: Treat all personal thoughts shared with respect and confidence.

Always maintain this balanced, uplifting, and grounded persona."""

    @staticmethod
    def get_system_prompt() -> str:
        return EmotionService.SYSTEM_PROMPT

    @staticmethod
    def detect_emotional_tone(text: str) -> Dict[str, Any]:
        """
        Lightweight heuristic sentiment and emotional tone tagger.
        """
        lower = text.lower()
        emotions = []

        if any(w in lower for w in ["sad", "unhappy", "crying", "depressed", "lonely", "hopeless", "grief"]):
            emotions.append("Sadness/Grief")
        if any(w in lower for w in ["anxious", "worried", "nervous", "stressed", "overwhelmed", "panic"]):
            emotions.append("Anxiety/Stress")
        if any(w in lower for w in ["angry", "mad", "furious", "annoyed", "frustrated"]):
            emotions.append("Frustration/Anger")
        if any(w in lower for w in ["happy", "excited", "grateful", "glad", "joy", "peaceful"]):
            emotions.append("Joy/Gratitude")
        if any(w in lower for w in ["tired", "exhausted", "burnout", "drained"]):
            emotions.append("Exhaustion/Burnout")

        primary = emotions[0] if emotions else "Neutral/Reflective"
        return {
            "primary_tone": primary,
            "detected_emotions": emotions,
            "requires_empathy_boost": primary in ["Sadness/Grief", "Anxiety/Stress", "Exhaustion/Burnout"]
        }

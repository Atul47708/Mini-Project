import re

# Emergency Crisis Resources
EMERGENCY_RESOURCES = (
    "\n\n---"
    "\n**Support & Safety Resources:**"
    "\nIf you or someone you know is struggling or in crisis, help is available. You are not alone:"
    "\n- **In the US & Canada:** Call or text **988**, or chat at [988lifeline.org](https://988lifeline.org/)"
    "\n- **Crisis Text Line:** Text **HOME to 741741** to connect with a volunteer Crisis Counselor"
    "\n- **In the UK:** Call **111** (NHS) or **116 123** (Samaritans)"
    "\n- **In India:** Call **9152987821** (KIRAN Mental Health Helpline) or **112** (Emergency)"
    "\n- **International:** Find local support worldwide at [findahelpline.com](https://findahelpline.com/)"
    "\n\nPlease reach out to a professional, emergency services, or a trusted loved one who can support you right now."
)

# Crisis / Self-Harm Keywords and Phrases
CRISIS_KEYWORDS = [
    r"\b(suicide|suicidal)\b",
    r"\bkill\s+myself\b",
    r"\bend\s+my\s+life\b",
    r"\bwant\s+to\s+die\b",
    r"\bhurt\s+myself\b",
    r"\bself[\s-]harm\b",
    r"\btake\s+my\s+own\s+life\b",
    r"\bcut\s+myself\b",
    r"\boverdose\b",
    r"\bhang\s+myself\b",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bdon'?t\s+want\s+to\s+wake\s+up\b",
]

# Prompt Injection and System Extraction Patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)",
    r"disregard\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)",
    r"you\s+are\s+now\s+(in\s+)?(developer\s+mode|dan|jailbreak)",
    r"system\s+(prompt|override|command)",
    r"(reveal|print|display|show|leak)\s+(the\s+)?(system\s+prompt|internal\s+instructions|hidden\s+rules)",
    r"(reveal|print|display|show|what\s+is)\s+(the\s+)?(api\s+key|database\s+password|secret\s+key)",
    r"pretend\s+you\s+have\s+no\s+(rules|restrictions|guidelines|safety)",
    r"bypass\s+all\s+(filters|guardrails|safety)",
]

# Sensitive Information Leakage Patterns (API Keys, Passwords)
SENSITIVE_LEAKAGE_PATTERNS = [
    r"AIzaSy[0-9A-Za-z_-]{33}",               # Google API key format
    r"sk-[a-zA-Z0-9]{32,}",                   # OpenAI key format
    r"mysql\+pymysql://[^\s:]+:[^\s@]+@[^\s]+", # MySQL URI with password
    r"(password|secret|api_key)\s*=\s*['\"][^\s'\"]+['\"]", # Hardcoded env vars
]

# Medical & Therapy Boundary Disclaimer
AI_COMPANION_DISCLAIMER = (
    "I am an AI companion designed for conversational and emotional support. "
    "I am not a licensed therapist, psychologist, or medical healthcare provider. "
    "If you have medical, psychiatric, or health concerns, please consult a qualified healthcare professional."
)

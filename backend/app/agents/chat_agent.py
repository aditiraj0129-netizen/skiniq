"""
Skincare Chat Agent: a scoped FAQ assistant using Groq's fast inference API.
System prompt keeps it focused on skincare topics and consistently
disclaims that it doesn't replace professional advice.
"""
import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"   # fast, free-tier friendly; swap to openai/gpt-oss-120b for stronger answers

SYSTEM_PROMPT = """You are SkinIQ's skincare FAQ assistant. You answer general,
educational questions about skincare: skin types (oily/dry/normal/combination),
common concerns (acne, dark circles, dryness, sensitivity), general ingredient
knowledge, sun protection, and everyday skincare routines.

Rules you always follow:
- Stay strictly on skincare/skin-health topics. If asked something unrelated,
  politely redirect back to skincare.
- Never diagnose a specific condition for the user or tell them they definitely
  have a condition -- speak in general, educational terms.
- Never recommend prescription-strength treatments or specific dosages.
- For anything that sounds like a real, persistent, or concerning symptom,
  clearly recommend seeing a licensed dermatologist.
- Keep answers concise, warm, and practical.
- End with a brief reminder that this is general information, not personalized
  medical advice, when relevant (not every single message needs the full disclaimer,
  use judgment).
"""


def ask_skincare_chatbot(user_message: str, conversation_history: list[dict] = None) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "reply": None,
            "error": "GROQ_API_KEY is not configured on the server. Set it in your .env file.",
        }

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history[-10:])  # keep recent context only, bounded
    messages.append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": GROQ_MODEL, "messages": messages, "temperature": 0.4, "max_tokens": 500},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return {"reply": reply, "error": None}
    except requests.exceptions.RequestException as e:
        return {"reply": None, "error": f"Chat service unavailable: {e}"}
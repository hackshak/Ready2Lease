from google import genai
from django.conf import settings
from action_plan.models import CompletedTask


def generate_ai_response(user, history, assessment):
    """
    Generate AI response using google-genai SDK
    """

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Get completed tasks
        completed_tasks = list(
            CompletedTask.objects
            .filter(user=user)
            .values_list("task_key", flat=True)
        )

        # Build prompt
        prompt = f"""
You are a rental readiness expert assistant for a SaaS platform called ReadyRent.

Selected Assessment Details:
- Readiness Score: {assessment.readiness_score}
- Risk Level: {assessment.risk_level}
- Suburb: {assessment.suburb}

Completed Tasks: {completed_tasks}

Your Responsibilities:
- Clearly explain the readiness score
- Identify strengths and weaknesses
- Suggest the next best improvement action
- Provide practical, actionable advice
- Help improve rental approval chances
- Keep responses structured and easy to understand

Conversation History:
"""

        for msg in history:
            role = "Assistant" if msg["role"] == "assistant" else "User"
            prompt += f"\n{role}: {msg['content']}"

        prompt += "\nAssistant:"

        response = client.models.generate_content(
            model="gemini-1.5-flash",   # IMPORTANT: use 1.5
            contents=prompt
        )

        if response and response.text:
            return response.text

        return "I'm unable to generate a response at the moment."

    except Exception as e:
        print("Gemini Error:", e)
        return "AI temporarily unavailable."
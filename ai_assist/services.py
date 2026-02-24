from openai import OpenAI
from django.conf import settings
from action_plan.models import CompletedTask


def generate_ai_response(user, history, assessment):
    """
    Generate AI response using DeepSeek API
    """

    try:
        client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"  # IMPORTANT
        )

        # Get completed tasks
        completed_tasks = list(
            CompletedTask.objects
            .filter(user=user)
            .values_list("task_key", flat=True)
        )

        # Build system message
        system_prompt = f"""
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
"""

        # Build messages list (chat format)
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Add conversation history
        for msg in history:
            messages.append({
                "role": msg["role"],  # must be "user" or "assistant"
                "content": msg["content"]
            })

        # Call DeepSeek model
        response = client.chat.completions.create(
            model="deepseek-chat",  # recommended model
            messages=messages,
            temperature=0.7,
            max_tokens=800
        )

        if response.choices:
            return response.choices[0].message.content

        return "I'm unable to generate a response at the moment."

    except Exception as e:
        print("DeepSeek Error:", e)
        return "AI temporarily unavailable."
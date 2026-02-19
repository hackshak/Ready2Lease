import openai
from openai import OpenAI
from django.conf import settings
from assessments.models import Assessment
from action_plan.models import CompletedTask


def build_ai_context(user):
    assessment = (
        Assessment.objects
        .filter(user=user)
        .order_by("-created_at")
        .first()
    )

    completed_tasks = CompletedTask.objects.filter(user=user)

    base_score = assessment.readiness_score if assessment else 0
    tasks = [t.task_key for t in completed_tasks]

    return {
        "score": base_score,
        "suburb": assessment.suburb if assessment else "",
        "risk_level": assessment.risk_level if assessment else "",
        "completed_tasks": tasks
    }







def generate_ai_response(user, history):

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    # Get latest assessment
    assessment = (
        Assessment.objects
        .filter(user=user)
        .order_by("-created_at")
        .first()
    )

    if not assessment:
        return "No assessment found. Please complete your readiness assessment first."

    completed_tasks = list(
        CompletedTask.objects
        .filter(user=user)
        .values_list("task_key", flat=True)
    )

    system_prompt = f"""
You are a rental readiness expert assistant for a SaaS platform called ReadyRent.

User readiness score: {assessment.readiness_score}
Risk level: {assessment.risk_level}

Completed tasks: {completed_tasks}

Your responsibilities:
- Explain score in simple language
- Suggest next best action
- Improve approval chances
- Help with cover letter
- Be practical and actionable
- Keep responses structured and clear
"""

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    for msg in history:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
    )

    return response.choices[0].message.content
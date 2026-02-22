from django.conf import settings
from google import genai


class CoverLetterGeneratorService:
    """
    AI-based cover letter generator using Google GenAI SDK.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def build_prompt(self, base_inputs: dict, tone: str, property_address: str = None):

        tone_map = {
            "professional": "Use a formal and polished tone.",
            "friendly": "Use a warm but professional tone.",
            "confident": "Use a confident and strong tone.",
            "direct": "Keep it concise and straight to the point.",
        }

        property_section = ""
        if property_address:
            property_section = f"""
            The applicant is applying for property at: {property_address}.
            Include a personalized sentence explaining interest in this property.
            """

        return f"""
You are a rental application expert.

Write a professional landlord-friendly rental cover letter.

Tone: {tone_map.get(tone, tone_map["professional"])}

Applicant Information:
- Name: {base_inputs.get("name")}
- Employment: {base_inputs.get("employment_info")}
- Income: {base_inputs.get("income")}
- Rental History: {base_inputs.get("rental_history")}
- Additional Notes: {base_inputs.get("custom_note")}

{property_section}

Requirements:
- Emphasize reliability and financial stability.
- Keep it between 250-400 words.
- No placeholders.
- Return only the final letter.
"""

    def generate_letter(self, base_inputs: dict, tone: str, property_address: str = None):

        prompt = self.build_prompt(base_inputs, tone, property_address)

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        if not response or not response.text:
            raise Exception("Failed to generate cover letter.")

        return response.text.strip()
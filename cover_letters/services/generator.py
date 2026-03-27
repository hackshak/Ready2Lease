from google import genai
from django.conf import settings


class CoverLetterGeneratorService:

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def build_prompt(self, base_inputs: dict, tone: str, property_address: str = None):

        tone_map = {
            "professional": "Use a formal and polished tone.",
            "friendly": "Use a warm but still professional tone.",
            "confident": "Use a confident and strong tone.",
            "direct": "Keep it concise and straight to the point.",
        }

        property_section = ""
        if property_address:
            property_section = f"""
Property Details:
The applicant is applying for the property located at:
{property_address}

Include a short sentence showing genuine interest in this property.
"""

        return f"""
You are an expert in writing rental application cover letters.

{tone_map.get(tone, tone_map["professional"])}

APPLICANT INFORMATION:
Name: {base_inputs.get("name")}
Employment Information: {base_inputs.get("employment_info")}
Income Details: {base_inputs.get("income")}
Rental History: {base_inputs.get("rental_history")}
Additional Notes: {base_inputs.get("custom_note")}

{property_section}

Write a professional rental application cover letter using HTML <p> tags.

Rules:
- No headings
- No markdown
- No bullet points
- Clean paragraphs
- 220–300 words
"""

    def generate_letter(self, base_inputs: dict, tone: str, property_address: str = None):

        prompt = self.build_prompt(base_inputs, tone, property_address)

        try:
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
            )

            # ✅ NEW SAFE PARSING
            if not response or not response.text:
                raise Exception("Empty response from Gemini")

            return response.text.strip()

        except Exception as e:
            raise Exception(f"Gemini Error: {str(e)}")

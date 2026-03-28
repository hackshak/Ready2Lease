import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


class CoverLetterGeneratorService:

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in settings.py")
        self.api_key = settings.GEMINI_API_KEY

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
- Clean paragraphs only
- 220-300 words
"""

    def generate_letter(self, base_inputs: dict, tone: str, property_address: str = None):

        prompt = self.build_prompt(base_inputs, tone, property_address)
        logger.info(f"Generating cover letter | tone={tone}")

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8192, 
                "topP": 0.95,
            }
        }

        try:
            response = requests.post(
                GEMINI_API_URL,
                params={"key": self.api_key},
                json=payload,
                timeout=60,
            )
            response.raise_for_status()

        except requests.exceptions.Timeout:
            logger.error("Gemini request timed out")
            raise Exception("Gemini request timed out after 60 seconds")

        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini network error: {e}")
            raise Exception(f"Network error calling Gemini: {str(e)}")

        try:
            data = response.json()
            generated_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected Gemini response format: {response.text[:300]}")
            raise Exception("Unexpected response format from Gemini")

        if not generated_text:
            raise Exception("Gemini returned empty text")

        logger.info(f"Gemini success — {len(generated_text)} characters generated")
        return generated_text
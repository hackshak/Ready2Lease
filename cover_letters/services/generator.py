from django.conf import settings
from google.genai import Client


class CoverLetterGeneratorService:

    def __init__(self):
        self.client = Client(api_key=settings.GEMINI_API_KEY)

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
    You are an expert in writing **rental application cover letters** that impress landlords and property managers.

    Your task is to create a **high-quality tenant cover letter** that highlights reliability, financial stability, and responsibility.

    TONE INSTRUCTION:
    {tone_map.get(tone, tone_map["professional"])}

    APPLICANT INFORMATION:
    Name: {base_inputs.get("name")}
    Employment Information: {base_inputs.get("employment_info")}
    Income Details: {base_inputs.get("income")}
    Rental History: {base_inputs.get("rental_history")}
    Additional Notes: {base_inputs.get("custom_note")}

    {property_section}

    LETTER STRUCTURE:

    Write the letter as a natural professional rental application cover letter.

    The letter should include:

    - A polite greeting to the landlord or property manager
    - A short introduction of the applicant
    - A paragraph explaining employment and financial stability
    - A paragraph describing rental history and responsibility
    - A short paragraph explaining why the applicant would be a good tenant
    - A polite closing paragraph

    IMPORTANT FORMATTING RULES:

    - Do NOT include headings like Introduction, About Me, or Closing
    - Write the letter as natural paragraphs
    - Format the response using HTML <p> tags
    - Keep the text clean and professional
    - No bullet points
    - No markdown
    - Return only the final cover letter

    Length requirement:
    220-300 words so the letter fits on one A4 PDF page.
    """

    def generate_letter(self, base_inputs: dict, tone: str, property_address: str = None):

        prompt = self.build_prompt(base_inputs, tone, property_address)

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        try:
            text = response.candidates[0].content.parts[0].text
        except (IndexError, AttributeError):
            raise Exception("Gemini returned an empty or malformed response")

        if not text or not text.strip():
            raise Exception("Gemini returned empty text")

        return text.strip()
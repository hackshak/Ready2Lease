# blog/services/gemini_service.py

from google import genai
from django.conf import settings
import json
import re

client = genai.Client(api_key=settings.GEMINI_API_KEY)


def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {}


def generate_blog(title, description, category):

    prompt = f"""
    Write a complete SEO optimized blog article.

    Title: {title}
    Description: {description}
    Category: {category}

    Requirements:
    - Maximum 200-350 words
    - SEO optimized
    - Use HTML formatting
    - Use H2 and H3 headings
    - Include introduction and conclusion

    Return JSON ONLY:

    {{
      "content":"",
      "meta_title":"",
      "meta_description":"",
      "meta_keywords":"",
      "slug":""
    }}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return extract_json(response.text)





        
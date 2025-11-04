# backend/ai_filter.py
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def parse_query_to_filters(user_query: str):
    """Send a natural language query to Gemini and get back structured filters."""
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
    Extract structured filters from this query:
    Query: "{user_query}"
    Available columns: ['sector', 'country', 'market_cap_billions', 'profit_margin', 'price', 'change_percent']

    Return JSON only, no explanation, in this format:
    {{
        "sector": "Technology",
        "country": "USA",
        "profit_margin": {{">": 0}}
    }}
    """

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Ensure valid JSON
        json_str = text[text.find("{") : text.rfind("}") + 1]
        filters = json.loads(json_str)
        return filters
    except Exception as e:
        print("[ERROR] Gemini parsing failed:", e)
        return {"error": str(e)}

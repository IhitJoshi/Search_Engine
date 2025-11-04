# backend/ai_parser.py
import google.generativeai as genai
import os
import json

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def parse_stock_query(user_query):
    prompt = f"""
You are a financial query parser. Convert the following natural language query into structured filters.

Query: "{user_query}"
Available columns: ['sector', 'country', 'market_cap_billions', 'profit_margin', 'price', 'change_percent']

Return ONLY JSON in this format:
{{
  "sector": "...",
  "country": "...",
  "profit_margin": {{">": 0}},
  "market_cap_billions": {{">": 50}}
}}
If information is missing, skip that field.
"""

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    try:
        json_str = response.text.strip().strip("`")
        return json.loads(json_str)
    except Exception as e:
        print("Error parsing Gemini output:", e, "\nOutput:", response.text)
        return {}

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
print("Loaded key:", bool(key))

genai.configure(api_key=key)

models = genai.list_models(page_size=20)
for m in models:
    print(m.name)

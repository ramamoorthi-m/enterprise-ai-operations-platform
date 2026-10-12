import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model = os.getenv("GEMINI_MODEL")

if not api_key or not model:
    raise SystemExit("GEMINI_API_KEY or GEMINI_MODEL is missing.")

client = genai.Client(api_key=api_key)

try:
    print(f"Checking model metadata: {model}")

    info = client.models.get(model=model)

    print("MODEL FOUND")
    print("Name:", info.name)
    print("Display name:", info.display_name)
    print("Input token limit:", info.input_token_limit)
    print("Output token limit:", info.output_token_limit)

except Exception as exc:
    print("MODEL CHECK FAILED")
    print(f"{type(exc).__name__}: {exc}")

finally:
    client.close()
from app.llm.client import GeminiClient

client = GeminiClient()

try:
    print("Testing one short Gemini generation...")
    response = client.generate(
        "Reply with exactly: GEMINI_OK"
    )
    print("Generation succeeded:", response)

except Exception as exc:
    print("Generation failed:")
    print(f"{type(exc).__name__}: {exc}")
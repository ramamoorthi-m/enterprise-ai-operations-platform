from app.llm.client import GeminiClient


client = GeminiClient()

response = client.generate(
    "In one sentence, explain what tool calling means in an AI agent."
)

print(response)
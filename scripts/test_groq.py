from app.llm.groq_client import GroqClient


def main():
    client = GroqClient(
        model="openai/gpt-oss-120b"
    )

    response = client.generate(
        "Explain in two sentences why evidence validation "
        "is important in an enterprise AI operations platform."
    )

    print("\nGroq response:\n")
    print(response)


if __name__ == "__main__":
    main()
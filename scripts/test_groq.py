from app.llm.groq_client import GroqClient


def main():
    client = GroqClient()

    response = client.generate(
        "Reply with exactly: Groq connection works."
    )

    print("\nGroq response:\n")
    print(response)


if __name__ == "__main__":
    main()
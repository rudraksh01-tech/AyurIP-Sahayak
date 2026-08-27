from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def generate_answer(query, retrieved_chunks):

    context = "\n\n".join(
        [
            f"Source: {chunk['source']}\n"
            f"Content: {chunk['text']}"
            for chunk in retrieved_chunks
        ]
    )

    prompt = f"""
You are AyurIP-Sahayak, an AI assistant for Ayurveda,
Traditional Knowledge and Intellectual Property Rights.

Answer the user's question using ONLY the provided context.

If the answer is not available in the context,
clearly say that the information was not found
in the provided documents.

Do not invent facts.

USER QUESTION:
{query}

CONTEXT:
{context}

Provide a clear and concise answer.
"""

    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )

    return interaction.output_text


if __name__ == "__main__":

    test_chunks = [
        {
            "source": "test",
            "text": "TKDL stands for Traditional Knowledge Digital Library."
        }
    ]

    answer = generate_answer(
        "What is TKDL?",
        test_chunks
    )

    print("\nANSWER:")
    print(answer)

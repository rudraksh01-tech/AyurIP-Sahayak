from rag.retrieval.retrieval import retrieve
from rag.generation.generator import generate_answer


def ask(question, top_k=5):

    print("\nRetrieving relevant documents...")

    chunks = retrieve(question, top_k=top_k)

    print(f"Retrieved {len(chunks)} chunks.")

    print("\nGenerating answer...")

    answer = generate_answer(question, chunks)

    return answer


if __name__ == "__main__":

    question = input("\nAsk your question: ")

    answer = ask(question)

    print("\n" + "=" * 60)
    print("FINAL ANSWER")
    print("=" * 60)
    print(answer)

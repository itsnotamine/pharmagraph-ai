from app.rag.retriever import HybridRetriever

def main():
    print("\n=== PHARMAGRAPH AI — HYBRID RAG TEST ===\n")

    retriever = HybridRetriever()
    retriever.build_index()

    questions = [
        "What are the main contraindications for warfarin?",
        "Compare the contraindications of warfarin and apixaban.",
        "What is the bleeding risk when combining warfarin and sertraline?",
        "Is metformin contraindicated at an eGFR of 25?"
    ]

    for question in questions:
        print("\n" + "=" * 70)
        print("QUESTION:", question)
        print("=" * 70)

        results = retriever.search(question, top_k=6)

        for i, result in enumerate(results, start=1):
            print(f"\nRESULT {i}")
            print("Source:", result["source"])
            print("Section:", result["section"])
            print("Score:", round(result["score"], 4))
            print("Excerpt:", result["text"][:300])

    print("\n=== TEST COMPLETED ===")


if __name__ == "__main__":
    main()
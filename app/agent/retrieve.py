from functools import lru_cache

from app.rag.retriever import HybridRetriever


@lru_cache(maxsize=1)
def get_retriever():
    retriever = HybridRetriever()
    retriever.build_index()
    return retriever


def retrieve_node(state: dict) -> dict:
    retriever = get_retriever()

    queries = (
        state.get("search_queries", [])
        + state.get("additional_queries", [])
    )

    if not queries:
        queries = [state["question"]]

    unique = {
        item["id"]: item
        for item in state.get("evidence", [])
    }

    for query in queries[:8]:
        results = retriever.search(query, top_k=8)

        for item in results:
            existing = unique.get(item["id"])

            if existing is None or item["score"] > existing["score"]:
                unique[item["id"]] = item

    evidence = sorted(
        unique.values(),
        key=lambda item: item["score"],
        reverse=True,
    )

    return {
        "evidence": evidence[:20],
        "additional_queries": [],
    }
from app.knowledge.retriever import GuideRetriever


def search_guides(query: str, top_k: int = 3) -> list[dict]:
    retriever = GuideRetriever()
    return [hit.to_dict() for hit in retriever.search(query=query, top_k=top_k)]


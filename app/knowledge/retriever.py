from dataclasses import asdict, dataclass
import re

from app.knowledge.loader import GuideDocument, load_guides


@dataclass(frozen=True)
class GuideHit:
    id: str
    title: str
    equipment: str
    source_path: str
    score: int
    snippet: str

    def to_dict(self) -> dict:
        return asdict(self)


class GuideRetriever:
    def __init__(self, documents: list[GuideDocument] | None = None) -> None:
        self.documents = documents if documents is not None else load_guides()

    def search(self, query: str, top_k: int = 3) -> list[GuideHit]:
        query_tokens = _tokens(query)
        hits: list[GuideHit] = []

        for document in self.documents:
            haystack = " ".join([document.title, document.equipment, document.content])
            doc_tokens = _tokens(haystack)
            score = len(query_tokens.intersection(doc_tokens))
            if score <= 0:
                continue

            hits.append(
                GuideHit(
                    id=document.id,
                    title=document.title,
                    equipment=document.equipment,
                    source_path=document.source_path,
                    score=score,
                    snippet=_snippet(document.content, query_tokens),
                )
            )

        hits.sort(key=lambda item: item.score, reverse=True)
        return hits[:top_k]


def _tokens(text: str) -> set[str]:
    lowered = text.lower()
    ascii_tokens = set(re.findall(r"[a-z0-9_]+", lowered))
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    cjk_bigrams = {cjk_chars[index] + cjk_chars[index + 1] for index in range(len(cjk_chars) - 1)}
    return {token for token in ascii_tokens.union(cjk_bigrams) if len(token) >= 2}


def _snippet(content: str, tokens: set[str], max_chars: int = 220) -> str:
    compact = " ".join(line.strip() for line in content.splitlines() if line.strip())
    if len(compact) <= max_chars:
        return compact

    for token in tokens:
        index = compact.lower().find(token.lower())
        if index >= 0:
            start = max(0, index - 60)
            end = min(len(compact), start + max_chars)
            return compact[start:end]

    return compact[:max_chars]


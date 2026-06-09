from pathlib import Path
from typing import Any
import json
import re


def search_cases(query: str, symptoms: list[str] | None = None, top_k: int = 3) -> list[dict[str, Any]]:
    query_tokens = _tokens(" ".join([query, " ".join(symptoms or [])]))
    hits: list[dict[str, Any]] = []

    for case in _load_cases():
        haystack = " ".join(
            [
                case.get("id", ""),
                case.get("title", ""),
                case.get("scenario", ""),
                " ".join(case.get("equipment", [])),
                " ".join(case.get("symptoms", [])),
                case.get("root_cause", ""),
                case.get("resolution", ""),
            ]
        )
        score = len(query_tokens.intersection(_tokens(haystack)))
        if score <= 0:
            continue

        item = dict(case)
        item["score"] = score
        hits.append(item)

    hits.sort(key=lambda item: item["score"], reverse=True)
    return hits[:top_k]


def _load_cases() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parents[2] / "data" / "cases.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _tokens(text: str) -> set[str]:
    lowered = text.lower()
    ascii_tokens = set(re.findall(r"[a-z0-9_]+", lowered))
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    cjk_bigrams = {cjk_chars[index] + cjk_chars[index + 1] for index in range(len(cjk_chars) - 1)}
    return {token for token in ascii_tokens.union(cjk_bigrams) if len(token) >= 2}

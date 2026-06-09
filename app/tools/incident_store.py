from pathlib import Path
from typing import Any
import json
import re


def list_incidents() -> list[dict[str, Any]]:
    return _load_incidents()


def get_incident(incident_id: str | None) -> dict[str, Any] | None:
    if not incident_id:
        return None

    normalized = incident_id.upper()
    for incident in _load_incidents():
        if incident["id"].upper() == normalized:
            return incident
    return None


def find_related_incident(query: str) -> dict[str, Any] | None:
    query_tokens = _tokens(query)
    best_incident = None
    best_score = 0

    for incident in _load_incidents():
        text = " ".join(
            [
                incident.get("id", ""),
                incident.get("title", ""),
                incident.get("equipment", ""),
                incident.get("component", ""),
                " ".join(incident.get("symptoms", [])),
            ]
        )
        score = len(query_tokens.intersection(_tokens(text)))
        if score > best_score:
            best_score = score
            best_incident = incident

    return best_incident


def _load_incidents() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parents[2] / "data" / "incidents.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _tokens(text: str) -> set[str]:
    lowered = text.lower()
    ascii_tokens = set(re.findall(r"[a-z0-9_]+", lowered))
    cjk_chars = re.findall(r"[\u4e00-\u9fff]", text)
    cjk_bigrams = {cjk_chars[index] + cjk_chars[index + 1] for index in range(len(cjk_chars) - 1)}
    return {token for token in ascii_tokens.union(cjk_bigrams) if len(token) >= 2}


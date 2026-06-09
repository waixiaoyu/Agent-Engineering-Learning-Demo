from pathlib import Path
from typing import Any
import json


def search_logs(component: str | None, limit: int = 10) -> list[dict[str, Any]]:
    logs = _load_logs()
    if component:
        logs = [item for item in logs if item.get("component") == component]
    return logs[:limit]


def _load_logs() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parents[2] / "data" / "logs.json"
    return json.loads(path.read_text(encoding="utf-8"))


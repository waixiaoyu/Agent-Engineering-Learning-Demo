from pathlib import Path
from typing import Any
import json


def get_metrics_snapshot(component: str | None) -> dict[str, Any]:
    snapshots = _load_metrics()
    if component:
        for snapshot in snapshots:
            if snapshot.get("component") == component:
                return snapshot
    return {"component": component, "metrics": {}, "thresholds": {}, "status": "not_found"}


def _load_metrics() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parents[2] / "data" / "metrics.json"
    return json.loads(path.read_text(encoding="utf-8"))


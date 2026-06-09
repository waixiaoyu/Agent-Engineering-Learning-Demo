from pathlib import Path
from typing import Any
import json


def query_device_status(equipment: list[str] | None = None) -> dict[str, Any]:
    statuses = _load_statuses()
    equipment_text = " ".join(equipment or [])

    result: dict[str, Any] = {"source": "demo_fixture", "devices": []}
    if "S380" in equipment_text or "eKitEngine" in equipment_text:
        result["devices"].append(statuses["s380-demo"])
    if "AP" in equipment_text:
        result["devices"].append(statuses["ap-demo"])

    if not result["devices"]:
        result["devices"].append(statuses["s380-demo"])

    result["note"] = "V1 使用示例设备状态展示 Tool Calling；真实设备接入放在后续版本。"
    return result


def _load_statuses() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[2] / "data" / "device_status.json"
    return json.loads(path.read_text(encoding="utf-8"))

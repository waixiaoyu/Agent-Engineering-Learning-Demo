from pathlib import Path
from typing import Any
import json


def build_onboarding_action_checks(
    symptoms: list[str],
    observations: dict[str, Any],
    runbook_hits: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    templates = _load_templates()
    selected: list[dict[str, Any]] = []

    for template in templates:
        if _should_include(template["id"], symptoms=symptoms, observations=observations):
            item = dict(template)
            item["status"] = "pending_user_check"
            item["source"] = "agent_generated_from_runbook"
            item["runbook_id"] = runbook_hits[0]["id"] if runbook_hits else None
            selected.append(item)

    return selected


def _should_include(template_id: str, symptoms: list[str], observations: dict[str, Any]) -> bool:
    if template_id in {"project_site_check", "sn_check"}:
        return True
    if template_id == "wan_address_check":
        return "dhcp" in observations or "S380 扫码添加后未上线" in symptoms
    if template_id == "internet_reachability_check":
        return "local_connectivity" in observations or "S380 扫码添加后未上线" in symptoms
    if template_id == "redeploy_after_long_wait":
        return "S380 扫码添加后未上线" in symptoms
    return False


def _load_templates() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parents[2] / "data" / "onboarding_action_templates.json"
    return json.loads(path.read_text(encoding="utf-8"))

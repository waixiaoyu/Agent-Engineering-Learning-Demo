from typing import Any


def checklist_score(answer: str, expected_items: list[str]) -> float:
    if not expected_items:
        return 1.0

    normalized = answer.lower()
    hits = sum(1 for item in expected_items if _loose_match(item, normalized))
    return hits / len(expected_items)


def _loose_match(item: str, answer: str) -> bool:
    tokens = [token for token in item.lower().replace("-", " ").split() if len(token) > 2]
    return any(token in answer for token in tokens)


def evaluate_agent_state(state: dict[str, Any]) -> dict[str, Any]:
    final_answer = state.get("final_answer", "")
    metrics = {
        "symptom_coverage": _bool_score(bool(state.get("symptoms"))),
        "evidence_usage": _bool_score(bool(state.get("runbook_hits") or state.get("case_hits") or state.get("device_status"))),
        "risk_awareness": _bool_score(bool(state.get("risk_signals")) or "风险" in final_answer),
        "actionability": _bool_score(len(state.get("recommended_actions", [])) >= 3),
        "escalation_condition": _bool_score("何时升级" in final_answer or "升级" in final_answer),
        "user_check_grounding": _bool_score(bool(state.get("onboarding_action_checks") or state.get("feedback_history"))),
    }
    score = round(sum(metrics.values()) / len(metrics), 2)
    return {
        "engine": "deepeval_local_fallback",
        "note": "V1 使用 DeepEval 风格指标做本地可运行评分；接入真实 DeepEval 时替换此 adapter。",
        "metrics": metrics,
        "score": score,
        "passed": score >= 0.75,
    }


def _bool_score(value: bool) -> float:
    return 1.0 if value else 0.0

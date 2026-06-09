from app.agent.state import AgentState


def reflection_node(state: AgentState) -> dict:
    reflection = {
        "has_equipment": bool(state.get("recognized_equipment")),
        "has_symptoms": bool(state.get("symptoms")),
        "has_evidence": bool(state.get("runbook_hits") or state.get("case_hits") or state.get("device_status")),
        "has_user_check_path": bool(state.get("onboarding_action_checks") or state.get("feedback_history")),
        "has_risk_control": _has_risk_control(state),
        "has_escalation_condition": True,
    }
    reflection["decision"] = "ready" if all(reflection.values()) else "need_more_evidence"

    return {
        "current_step": "reflect",
        "workflow": state.get("workflow", []) + ["reflect"],
        "reflection": reflection,
        "loop_history": state.get("loop_history", [])
        + [
            {
                "step": "reflect",
                "action": reflection["decision"],
                "reason": "输出前检查设备、现象、证据、用户核对路径、风险控制和升级条件。",
            }
        ],
    }


def _has_risk_control(state: AgentState) -> bool:
    actions = " ".join(state.get("recommended_actions", []))
    return "不要一开始就恢复出厂" in actions or "高风险" in actions or "不需要回退" in actions

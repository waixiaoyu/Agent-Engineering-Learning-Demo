import json
from typing import Any

from app.agent.state import AgentState
from app.llm.models import build_chat_model, llm_status


VALID_NEXT_ACTIONS = {"ask_user", "investigate", "investigate_remaining_risk"}


def decide_next_action_node(state: AgentState) -> dict:
    fallback_next_action = state.get("next_action", "investigate")
    llm_result = _try_llm_plan(state, fallback_next_action)
    next_action = fallback_next_action

    if llm_result.get("ok") and llm_result.get("next_action") in VALID_NEXT_ACTIONS:
        next_action = llm_result["next_action"]

    return {
        "current_step": "decide_next_action",
        "workflow": state.get("workflow", []) + ["decide_next_action"],
        "next_action": next_action,
        "llm": {
            **state.get("llm", {}),
            "planner": llm_result,
            "status": llm_status(),
        },
        "tool_calls": _append_llm_call(state, llm_result),
        "loop_history": state.get("loop_history", [])
        + [
            {
                "step": "decide_next_action",
                "action": next_action,
                "reason": _plan_reason(llm_result, fallback_next_action, next_action),
            }
        ],
    }


def _try_llm_plan(state: AgentState, fallback_next_action: str) -> dict:
    model = build_chat_model()
    if not model:
        return {
            "ok": False,
            "reason": "llm_not_configured",
            "fallback_next_action": fallback_next_action,
            "provider": llm_status(),
        }

    prompt_state: dict[str, Any] = {
        "scenario": state.get("scenario"),
        "recognized_equipment": state.get("recognized_equipment", []),
        "symptoms": state.get("symptoms", []),
        "observations": state.get("observations", {}),
        "risk_signals": state.get("risk_signals", []),
        "missing_info": state.get("missing_info", []),
        "feedback_history": state.get("feedback_history", []),
        "fallback_next_action": fallback_next_action,
        "available_actions": sorted(VALID_NEXT_ACTIONS),
    }
    messages = [
        {
            "role": "system",
            "content": (
                "你是故障运维 Agent 的规划节点。请基于当前 State 选择下一步动作，"
                "只能输出 JSON，不能编造真实 APP 日志或真实设备接口数据。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请输出 JSON，字段包含 next_action、reason、recommended_tools。"
                "next_action 只能是 ask_user、investigate、investigate_remaining_risk 之一。"
                "recommended_tools 可包含 runbook_search、case_search、device_status_query、ask_onboarding_action_check。"
                f"\n\nSTATE:\n{json.dumps(prompt_state, ensure_ascii=False, indent=2)}"
            ),
        },
    ]

    try:
        data = model.complete_json(messages, max_tokens=900)
        next_action = str(data.get("next_action") or fallback_next_action)
        recommended_tools = data.get("recommended_tools") or []
        if next_action not in VALID_NEXT_ACTIONS:
            next_action = fallback_next_action
        if not isinstance(recommended_tools, list):
            recommended_tools = []
        return {
            "ok": True,
            "provider": llm_status(),
            "next_action": next_action,
            "reason": str(data.get("reason") or ""),
            "recommended_tools": [str(item) for item in recommended_tools],
            "fallback_next_action": fallback_next_action,
        }
    except Exception as exc:
        return {
            "ok": False,
            "reason": "llm_error",
            "error": str(exc),
            "fallback_next_action": fallback_next_action,
            "provider": llm_status(),
        }


def _append_llm_call(state: AgentState, llm_result: dict) -> list[dict]:
    if llm_result.get("reason") == "llm_not_configured":
        return state.get("tool_calls", [])
    return state.get("tool_calls", []) + [
        {
            "tool": "llm.glm.decide_next_action",
            "input": {"node": "decide_next_action", "provider": llm_result.get("provider")},
            "output": {
                "ok": llm_result.get("ok"),
                "next_action": llm_result.get("next_action"),
                "reason": llm_result.get("reason"),
                "recommended_tools": llm_result.get("recommended_tools"),
                "error": llm_result.get("error"),
            },
        }
    ]


def _plan_reason(llm_result: dict, fallback_next_action: str, next_action: str) -> str:
    if llm_result.get("ok"):
        reason = llm_result.get("reason") or "GLM 根据当前 State 选择下一步动作。"
        return f"{reason} 本地兜底建议为 {fallback_next_action}，最终动作是 {next_action}。"
    if llm_result.get("reason") == "llm_not_configured":
        return f"未配置 GLM，使用本地规则规划下一步：{fallback_next_action}。"
    return f"GLM 规划调用失败，回退到本地规则：{fallback_next_action}。"

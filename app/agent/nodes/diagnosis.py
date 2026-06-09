import json

from app.agent.state import AgentState
from app.llm.models import build_chat_model, llm_status


def diagnosis_node(state: AgentState) -> dict:
    feedback_history = state.get("feedback_history", [])
    if feedback_history and feedback_history[-1].get("ap_topology") == "missing":
        diagnosis = "S380 上线问题已缓解，剩余风险转移到 AP 接入、AP 在线状态、整网自动发现和拓扑刷新。"
        possible_causes = _remaining_ap_causes()
        actions = _remaining_ap_actions()
    else:
        possible_causes = _s380_causes(state)
        diagnosis = "本地基础链路和 DHCP 有可用迹象，但 S380 仍等待上线，优先怀疑项目归属/SN、WAN 地址获取或外网通信条件。"
        actions = _s380_actions(state)

    llm_result = _try_llm_diagnosis(state, diagnosis, possible_causes, actions)
    if llm_result.get("ok"):
        diagnosis = llm_result["diagnosis"]
        possible_causes = llm_result["possible_causes"]
        actions = llm_result["recommended_actions"]

    return {
        "current_step": "diagnose",
        "workflow": state.get("workflow", []) + ["diagnose"],
        "diagnosis": diagnosis,
        "possible_causes": possible_causes,
        "recommended_actions": actions,
        "llm": {
            **state.get("llm", {}),
            "diagnosis": llm_result,
            "status": llm_status(),
        },
        "tool_calls": _append_llm_call(state, llm_result),
        "loop_history": state.get("loop_history", [])
        + [
            {
                "step": "diagnose",
                "action": "rank_causes_and_plan_actions",
                "reason": "根据 runbook、相似案例、设备状态和用户核对项排序原因；配置 GLM 时由模型辅助总结。",
            }
        ],
    }


def _s380_causes(state: AgentState) -> list[dict]:
    return [
        {
            "cause": "设备已在其他项目中或当前项目/SN 不一致",
            "rank": 1,
            "evidence": "APP 可扫码添加但等待上线；相似案例提示项目归属需要核对。",
        },
        {
            "cause": "WAN 地址获取或外网通信条件不满足",
            "rank": 2,
            "evidence": "官方排查路径要求保证 WAN 地址获取和外网通信；示例状态仍为 waiting_online。",
        },
        {
            "cause": "等待过久导致需要断电重启后重新部署",
            "rank": 3,
            "evidence": "官方资料提到等待过久时可断电重启后重新部署。",
        },
        {
            "cause": "S380 上线前 AP 拓扑无法完成发现",
            "rank": 4,
            "evidence": "AP 未出现在拓扑可能是 S380 未上线后的后续现象。",
        },
    ]


def _s380_actions(state: AgentState) -> list[str]:
    actions = [
        "先核对华为坤灵 APP 当前项目、门店和设备 SN，确认目标项目正确。",
        "确认 S380 是否曾加入其他项目；如果 APP 提示迁移，应按提示迁移到当前项目。",
        "核对 S380 WAN 口地址获取方式，默认 DHCP 场景下保持 DHCP 可用。",
        "确认 S380 具备外网通信条件；电脑能上网只能作为辅助证据，仍需观察设备是否自动上线。",
        "如果长时间 waiting online，按官方建议断电重启后重新部署并观察。",
        "不要一开始就恢复出厂；高风险操作前先保留现场配置记录并转人工确认。",
    ]
    checks = state.get("onboarding_action_checks", [])
    if checks:
        actions.append("请现场按“开局动作核对项”逐条回填结果，Agent 会基于回填继续下一轮判断。")
    return actions


def _remaining_ap_causes() -> list[dict]:
    return [
        {
            "cause": "AP 未上线或下联链路未满足",
            "rank": 1,
            "evidence": "用户反馈 S380 已上线，但 AP 仍未出现在拓扑。",
        },
        {
            "cause": "整网自动发现或拓扑刷新尚未完成",
            "rank": 2,
            "evidence": "官方资料支持 S380 上线后整网发现，下游 AP 需要继续确认。",
        },
    ]


def _remaining_ap_actions() -> list[str]:
    return [
        "确认 AP 是否接入 S380 下联网络，端口是否有链路状态。",
        "查询或现场确认 AP 是否已经上线。",
        "如果 AP 未上线，继续核对 DHCP 地址获取和出口访问。",
        "如果 AP 已上线但拓扑不显示，等待拓扑刷新或检查整网自动发现相关配置。",
        "当前不需要回退 S380 开局流程，问题焦点已经转到 AP 接入和拓扑发现。",
    ]


def _try_llm_diagnosis(
    state: AgentState,
    fallback_diagnosis: str,
    fallback_causes: list[dict],
    fallback_actions: list[str],
) -> dict:
    model = build_chat_model()
    if not model:
        return {
            "ok": False,
            "reason": "llm_not_configured",
            "provider": llm_status(),
        }

    prompt_state = {
        "scenario": state.get("scenario"),
        "recognized_equipment": state.get("recognized_equipment", []),
        "symptoms": state.get("symptoms", []),
        "observations": state.get("observations", {}),
        "risk_signals": state.get("risk_signals", []),
        "runbook_hits": state.get("runbook_hits", []),
        "case_hits": state.get("case_hits", []),
        "device_status": state.get("device_status", {}),
        "onboarding_action_checks": state.get("onboarding_action_checks", []),
        "feedback_history": state.get("feedback_history", []),
        "fallback": {
            "diagnosis": fallback_diagnosis,
            "possible_causes": fallback_causes,
            "recommended_actions": fallback_actions,
        },
    }
    messages = [
        {
            "role": "system",
            "content": (
                "你是故障运维 Agent 的诊断节点。请基于证据输出 JSON，不能编造真实 APP 日志。"
                "开局动作核对项是让用户现场确认的清单，不是系统查询到的日志。"
                "保持建议安全，不要一开始建议恢复出厂。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请生成诊断 JSON，字段必须包含 diagnosis、possible_causes、recommended_actions。"
                "possible_causes 每项包含 rank、cause、evidence。"
                f"\n\nSTATE:\n{json.dumps(prompt_state, ensure_ascii=False, indent=2)}"
            ),
        },
    ]

    try:
        data = model.complete_json(messages, max_tokens=1800)
        diagnosis = str(data.get("diagnosis") or fallback_diagnosis)
        possible_causes = data.get("possible_causes") or fallback_causes
        recommended_actions = data.get("recommended_actions") or fallback_actions
        if not isinstance(possible_causes, list) or not isinstance(recommended_actions, list):
            raise RuntimeError("LLM JSON fields have invalid types.")
        return {
            "ok": True,
            "provider": llm_status(),
            "diagnosis": diagnosis,
            "possible_causes": possible_causes,
            "recommended_actions": [str(item) for item in recommended_actions],
        }
    except Exception as exc:
        return {
            "ok": False,
            "reason": "llm_error",
            "error": str(exc),
            "provider": llm_status(),
        }


def _append_llm_call(state: AgentState, llm_result: dict) -> list[dict]:
    if llm_result.get("reason") == "llm_not_configured":
        return state.get("tool_calls", [])
    return state.get("tool_calls", []) + [
        {
            "tool": "llm.glm.chat_completion",
            "input": {"node": "diagnose", "provider": llm_result.get("provider")},
            "output": {
                "ok": llm_result.get("ok"),
                "reason": llm_result.get("reason"),
                "error": llm_result.get("error"),
            },
        }
    ]

import json
from typing import Any

from app.agent.state import AgentState
from app.llm.models import build_chat_model, llm_status


def understand_symptom_node(state: AgentState) -> dict:
    user_input = state.get("user_input") or state.get("question", "")
    equipment = _merge_unique(state.get("recognized_equipment", []), _recognize_equipment(user_input))
    symptoms = _merge_unique(state.get("symptoms", []), _recognize_symptoms(user_input))
    observations = {**state.get("observations", {}), **_extract_observations(user_input)}
    feedback = _extract_feedback(user_input)
    feedback_history = state.get("feedback_history", [])
    if feedback:
        feedback_history = feedback_history + [feedback]

    scenario = "华为坤灵 APP 开局" if _contains_any(user_input, ["坤灵", "eKit", "开局", "扫码"]) else state.get("scenario", "故障运维")
    risk_signals = _merge_unique(state.get("risk_signals", []), _recognize_risk_signals(user_input, symptoms))
    missing_info = _missing_info(symptoms=symptoms, observations=observations, feedback=feedback)
    next_action = "ask_user" if missing_info else "investigate"
    if feedback:
        next_action = "investigate_remaining_risk"

    llm_result = _try_llm_understand(
        user_input=user_input,
        fallback={
            "scenario": scenario,
            "recognized_equipment": equipment,
            "symptoms": symptoms,
            "observations": observations,
            "risk_signals": risk_signals,
            "missing_info": missing_info,
            "next_action": next_action,
        },
    )
    if llm_result.get("ok"):
        scenario = str(llm_result.get("scenario") or scenario)
        equipment = _merge_unique(equipment, _as_str_list(llm_result.get("recognized_equipment")))
        symptoms = _merge_unique(symptoms, _as_str_list(llm_result.get("symptoms")))
        observations = {**observations, **_as_dict(llm_result.get("observations"))}
        risk_signals = _merge_unique(risk_signals, _as_str_list(llm_result.get("risk_signals")))
        llm_missing_info = _as_str_list(llm_result.get("missing_info"))
        if llm_missing_info:
            missing_info = llm_missing_info
        candidate_next_action = str(llm_result.get("next_action") or next_action)
        if candidate_next_action not in {"ask_user", "investigate", "investigate_remaining_risk"}:
            candidate_next_action = next_action
        if candidate_next_action == "ask_user" or not missing_info:
            next_action = candidate_next_action
        if feedback:
            next_action = "investigate_remaining_risk"

    turn = {
        "role": "user",
        "content": user_input,
        "recognized_equipment": equipment,
        "symptoms": symptoms,
        "missing_info": missing_info,
    }

    return {
        "current_step": "understand_symptom",
        "workflow": state.get("workflow", []) + ["understand_symptom"],
        "scenario": scenario,
        "recognized_equipment": equipment,
        "symptoms": symptoms,
        "observations": observations,
        "risk_signals": risk_signals,
        "missing_info": missing_info,
        "feedback_history": feedback_history,
        "conversation_turns": state.get("conversation_turns", []) + [turn],
        "next_action": next_action,
        "llm": {
            **state.get("llm", {}),
            "understanding": llm_result,
            "status": llm_status(),
        },
        "tool_calls": _append_llm_call(state, llm_result),
        "loop_history": state.get("loop_history", [])
        + [
            {
                "step": "understand_symptom",
                "action": next_action,
                "reason": _reason_for_next_action(next_action, missing_info, feedback, llm_result),
            }
        ],
    }


def ask_clarifying_question_node(state: AgentState) -> dict:
    missing_info = state.get("missing_info", [])
    questions = _build_questions(missing_info)
    lines = [
        "我先按“华为坤灵 APP 开局 + eKitEngine S380 未上线 + AP 未出现在拓扑”来理解。",
        "",
        "现在还不适合直接下结论，因为现场关键信息不足。请先确认：",
    ]
    lines.extend(f"{index}. {question}" for index, question in enumerate(questions, start=1))
    lines.extend(
        [
            "",
            "这些信息会进入 AgentState，下一轮我再决定是查基础排查知识、相似案例、设备状态，还是生成开局动作核对项。",
        ]
    )

    return {
        "current_step": "ask_clarifying_question",
        "workflow": state.get("workflow", []) + ["ask_clarifying_question"],
        "final_answer": "\n".join(lines),
        "loop_history": state.get("loop_history", [])
        + [
            {
                "step": "ask_clarifying_question",
                "action": "ask_user",
                "reason": "信息不足，当前轮结束，等待用户补充现场信息。",
            }
        ],
    }


def intake_node(state: AgentState) -> dict:
    return understand_symptom_node(state)


def _try_llm_understand(user_input: str, fallback: dict[str, Any]) -> dict:
    model = build_chat_model()
    if not model:
        return {
            "ok": False,
            "reason": "llm_not_configured",
            "fallback": fallback,
            "provider": llm_status(),
        }

    messages = [
        {
            "role": "system",
            "content": (
                "你是故障运维 Agent 的理解节点。请把用户输入结构化为 AgentState 的关键字段。"
                "只能输出 JSON，不能编造真实 APP 日志、真实设备接口返回或未给出的现场事实。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请输出 JSON，字段包含 scenario、recognized_equipment、symptoms、observations、"
                "risk_signals、missing_info、next_action、reason。"
                "next_action 只能是 ask_user、investigate、investigate_remaining_risk。"
                f"\n\nUSER_INPUT:\n{user_input}"
                f"\n\nFALLBACK_RULE_OUTPUT:\n{json.dumps(fallback, ensure_ascii=False, indent=2)}"
            ),
        },
    ]

    try:
        data = model.complete_json(messages, max_tokens=1200)
        return {
            "ok": True,
            "provider": llm_status(),
            "scenario": str(data.get("scenario") or fallback.get("scenario") or ""),
            "recognized_equipment": _as_str_list(data.get("recognized_equipment")),
            "symptoms": _as_str_list(data.get("symptoms")),
            "observations": _as_dict(data.get("observations")),
            "risk_signals": _as_str_list(data.get("risk_signals")),
            "missing_info": _as_str_list(data.get("missing_info")),
            "next_action": str(data.get("next_action") or fallback.get("next_action") or "investigate"),
            "reason": str(data.get("reason") or ""),
            "fallback": fallback,
        }
    except Exception as exc:
        return {
            "ok": False,
            "reason": "llm_error",
            "error": str(exc),
            "fallback": fallback,
            "provider": llm_status(),
        }


def _append_llm_call(state: AgentState, llm_result: dict) -> list[dict]:
    if llm_result.get("reason") == "llm_not_configured":
        return state.get("tool_calls", [])
    return state.get("tool_calls", []) + [
        {
            "tool": "llm.glm.understand_symptom",
            "input": {"node": "understand_symptom", "provider": llm_result.get("provider")},
            "output": {
                "ok": llm_result.get("ok"),
                "scenario": llm_result.get("scenario"),
                "recognized_equipment": llm_result.get("recognized_equipment"),
                "symptoms": llm_result.get("symptoms"),
                "missing_info": llm_result.get("missing_info"),
                "next_action": llm_result.get("next_action"),
                "reason": llm_result.get("reason"),
                "error": llm_result.get("error"),
            },
        }
    ]


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _recognize_equipment(text: str) -> list[str]:
    equipment: list[str] = []
    if _contains_any(text, ["S380", "eKitEngine"]):
        equipment.append("eKitEngine S380")
    if _contains_any(text, ["AP", "无线"]):
        equipment.append("AP")
    if _contains_any(text, ["坤灵", "eKit App", "APP"]):
        equipment.append("华为坤灵 APP")
    if _contains_any(text, ["路由器", "网关", "光猫"]):
        equipment.append("上联网关")
    return equipment


def _recognize_symptoms(text: str) -> list[str]:
    symptoms: list[str] = []
    if _contains_any(text, ["未上线", "等待上线", "waiting online"]):
        symptoms.append("S380 扫码添加后未上线")
    if _contains_any(text, ["添加失败", "扫码失败"]):
        symptoms.append("APP 扫码添加失败")
    if "AP" in text and _contains_any(text, ["拓扑", "没有出现", "不进", "不显示"]):
        symptoms.append("AP 未出现在拓扑")
    if _contains_any(text, ["已经上线", "上线了"]) and "S380" in text:
        symptoms.append("S380 已上线")
    return symptoms


def _extract_observations(text: str) -> dict[str, object]:
    observations: dict[str, object] = {}
    if _contains_any(text, ["上联", "LAN", "路由器", "网关"]):
        observations["topology"] = "S380 上联信息已提供"
    if _contains_any(text, ["电源灯", "常亮"]):
        observations["power_indicator"] = "电源灯状态已提供"
    if _contains_any(text, ["上联口", "灯闪", "链路灯"]):
        observations["uplink_indicator"] = "上联口链路状态已提供"
    if _contains_any(text, ["DHCP", "自动分配"]):
        observations["dhcp"] = "现场提到 DHCP"
    if _contains_any(text, ["能上网", "访问互联网"]):
        observations["local_connectivity"] = "现场电脑可通过 S380 上网"
    if _contains_any(text, ["扫码能添加", "能添加设备", "扫码添加成功", "扫码添加"]):
        observations["app_add"] = "APP 可扫码添加设备"
    if _mentions_app_status(text):
        observations["app_status"] = "APP 显示未上线或等待上线"
    if "AP" in text and _contains_any(text, ["接在", "下联", "下面"]):
        observations["ap_access"] = "AP 接入位置已提供"
    return observations


def _extract_feedback(text: str) -> dict[str, object] | None:
    if not _contains_any(text, ["查了", "执行", "迁移", "已经上线", "上线了"]):
        return None

    feedback: dict[str, object] = {"raw": text}
    if _contains_any(text, ["迁移", "当前项目"]):
        feedback["action_taken"] = "按提示迁移到当前项目"
    if "S380" in text and _contains_any(text, ["已经上线", "上线了"]):
        feedback["switch_status"] = "online"
    if "AP" in text and _contains_any(text, ["还是没有", "仍", "没有出现", "不显示"]):
        feedback["ap_topology"] = "missing"
    return feedback


def _recognize_risk_signals(text: str, symptoms: list[str]) -> list[str]:
    risks = []
    if symptoms:
        risks.append("开局无法完成")
    if _contains_any(text, ["门店", "交付", "新门店"]):
        risks.append("门店网络交付受阻")
    if _contains_any(text, ["恢复出厂", "清空配置"]):
        risks.append("高风险操作待确认")
    return risks


def _missing_info(symptoms: list[str], observations: dict[str, object], feedback: dict[str, object] | None) -> list[str]:
    if feedback:
        return []

    missing: list[str] = []
    if symptoms and "topology" not in observations:
        missing.append("网络拓扑")
    if "power_indicator" not in observations or "uplink_indicator" not in observations:
        missing.append("指示灯状态")
    if "app_status" not in observations and "app_add" not in observations:
        missing.append("APP 状态")
    if "local_connectivity" not in observations:
        missing.append("网络连通性")
    if "dhcp" not in observations:
        missing.append("DHCP 状态")
    if "AP 未出现在拓扑" in symptoms and "ap_access" not in observations:
        missing.append("AP 接入口")
    return missing


def _build_questions(missing_info: list[str]) -> list[str]:
    question_map = {
        "网络拓扑": "S380 上联到哪里？是门店路由器、光猫，还是其他网关设备？",
        "指示灯状态": "S380 电源灯、上联口和 AP 下联口指示灯状态如何？",
        "APP 状态": "APP 里显示的是“未上线”“添加失败”，还是没有发现设备？",
        "网络连通性": "现场电脑接到 S380 下是否能上网？",
        "DHCP 状态": "现场网络是否使用 DHCP 自动分配地址？",
        "AP 接入口": "AP 接在哪个 S380 下联口？下联口是否有链路状态？",
    }
    return [question_map[item] for item in missing_info if item in question_map]


def _reason_for_next_action(
    next_action: str,
    missing_info: list[str],
    feedback: dict[str, object] | None,
    llm_result: dict | None = None,
) -> str:
    if llm_result and llm_result.get("ok"):
        reason = llm_result.get("reason") or "GLM 已将用户输入结构化为设备、现象、缺失信息和下一步动作。"
        return f"{reason} 本地规则同时保留为兜底校验。"
    if llm_result and llm_result.get("reason") == "llm_error":
        return "GLM 理解调用失败，使用本地规则结构化用户输入。"
    if feedback:
        return "用户提供了处置反馈，需要聚焦剩余风险继续诊断。"
    if next_action == "ask_user":
        return f"缺少 {', '.join(missing_info)}，证据不足。"
    return "现场信息足够进入证据查询和开局动作核对。"


def _merge_unique(left: list[str], right: list[str]) -> list[str]:
    merged = list(left)
    for item in right:
        if item not in merged:
            merged.append(item)
    return merged


def _contains_any(text: str, needles: list[str]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def _mentions_app_status(text: str) -> bool:
    if _contains_any(text, ["一直显示未上线", "等待上线", "显示的是未上线", "显示未上线"]):
        return True
    return "app" in text.lower() and _contains_any(text, ["未上线", "上线中", "添加失败", "没有发现设备"])

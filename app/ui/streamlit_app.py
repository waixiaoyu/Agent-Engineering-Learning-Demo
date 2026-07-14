import os
from typing import Any

import streamlit as st

try:
    from api_client import BackendConnectionError, get_backend_status, send_chat_message
except ModuleNotFoundError:
    from app.ui.api_client import BackendConnectionError, get_backend_status, send_chat_message


DEFAULT_PROMPT = "我们在新门店用华为坤灵 APP 开局，扫码添加 eKitEngine S380 后一直显示设备未上线，AP 也没有出现在拓扑里。现场说网线都插好了，帮我判断一下先查什么？"
FOLLOWUP_PROMPT = "S380 上联到门店路由器 LAN 口，电源灯常亮，上联口有灯闪。AP 接在 S380 下面。APP 里扫码能添加设备，但是一直显示未上线。现场电脑接到 S380 下面能上网，路由器开了 DHCP。"
FEEDBACK_PROMPT = "我们查了，S380 之前被另一个测试项目加过。按提示迁移到当前项目后，S380 已经上线了，但 AP 还是没有出现在拓扑里。"

STEP_LABELS = {
    "understand_symptom": "理解现象",
    "decide_next_action": "决定下一步",
    "ask_clarifying_question": "追问关键信息",
    "collect_evidence": "查询证据",
    "diagnose": "形成诊断",
    "reflect": "自我检查",
    "final": "生成回答",
    "evaluate": "质量评测",
}

STEP_PURPOSES = {
    "understand_symptom": "把用户的一句话拆成设备、现象、现场信息和风险信号。",
    "decide_next_action": "判断现在应该继续追问，还是已经可以去查知识、案例和设备状态。",
    "ask_clarifying_question": "信息还不够时，先问一线人员最关键的现场问题。",
    "collect_evidence": "调用后端工具，查基础排查知识、历史案例和示例设备状态。",
    "diagnose": "基于证据排序可能原因，并生成可执行的排查建议。",
    "reflect": "在输出前检查证据是否足够、步骤是否安全、是否需要升级处理。",
    "final": "把中间判断整理成一线人员能读懂的答复。",
    "evaluate": "用简单指标检查回答是否覆盖现象、使用证据、可执行且有风险意识。",
}

STEP_IO_CONTRACTS = {
    "understand_symptom": {
        "input": [
            ("user_input", "本轮用户原话，来自 FastAPI /chat 的 message"),
            ("previous_state", "上一轮保留下来的 AgentState，用于多轮上下文"),
            ("GLM / local rules", "GLM 负责辅助结构化理解；未配置 Key 时用本地规则兜底"),
        ],
        "output": [
            ("scenario", "识别到的业务场景"),
            ("recognized_equipment", "识别到的设备或系统对象"),
            ("symptoms", "结构化后的故障现象"),
            ("observations", "用户已经提供的现场事实"),
            ("missing_info", "还缺哪些关键信息"),
            ("next_action", "初步下一步动作"),
        ],
        "sample_output_paths": ["scenario", "recognized_equipment", "symptoms", "observations", "missing_info", "next_action"],
    },
    "decide_next_action": {
        "input": [
            ("scenario / symptoms", "上一步理解出的场景和故障现象"),
            ("observations", "已经掌握的现场信息"),
            ("missing_info", "仍然缺失的信息"),
            ("feedback_history", "用户是否反馈了上一轮处置结果"),
        ],
        "output": [
            ("next_action", "ask_user、investigate 或 investigate_remaining_risk"),
            ("llm.planner", "模型或规则给出的规划理由"),
            ("loop_history", "供页面展示的决策原因"),
        ],
        "sample_output_paths": ["next_action", "llm.planner", "loop_history"],
    },
    "ask_clarifying_question": {
        "input": [
            ("missing_info", "缺失信息列表"),
            ("question_map", "缺失字段到自然语言问题的映射"),
        ],
        "output": [
            ("final_answer", "本轮追问用户的问题"),
            ("loop_history", "记录为什么本轮要追问"),
        ],
        "sample_output_paths": ["missing_info", "final_answer"],
    },
    "collect_evidence": {
        "input": [
            ("user_input / scenario", "用于构造查询语句"),
            ("recognized_equipment / symptoms", "用于查知识、案例和设备状态"),
            ("observations", "用于生成现场核对项"),
        ],
        "output": [
            ("runbook_hits", "命中的基础排查知识"),
            ("case_hits", "命中的历史案例"),
            ("device_status", "示例设备状态"),
            ("onboarding_action_checks", "让用户现场核对的开局动作排查项"),
            ("evidence", "统一证据集合"),
            ("tool_calls", "工具调用记录"),
        ],
        "sample_output_paths": ["runbook_hits", "case_hits", "device_status", "onboarding_action_checks"],
    },
    "diagnose": {
        "input": [
            ("runbook_hits", "基础知识证据"),
            ("case_hits", "相似案例证据"),
            ("device_status", "设备状态证据"),
            ("onboarding_action_checks", "用户需要现场核对的动作"),
            ("feedback_history", "上一轮处置反馈"),
        ],
        "output": [
            ("diagnosis", "当前诊断结论"),
            ("possible_causes", "可能原因排序"),
            ("recommended_actions", "建议处置步骤"),
            ("llm.diagnosis", "GLM 辅助诊断结果或本地兜底原因"),
        ],
        "sample_output_paths": ["diagnosis", "possible_causes", "recommended_actions", "llm.diagnosis"],
    },
    "reflect": {
        "input": [
            ("recognized_equipment / symptoms", "是否已经明确对象和现象"),
            ("runbook_hits / case_hits / device_status", "是否已有证据支撑"),
            ("recommended_actions", "建议是否包含风险控制"),
        ],
        "output": [
            ("reflection", "自我检查 checklist"),
            ("reflection.decision", "ready 或 need_more_evidence"),
        ],
        "sample_output_paths": ["reflection"],
    },
    "final": {
        "input": [
            ("diagnosis", "诊断结论"),
            ("possible_causes", "可能原因排序"),
            ("recommended_actions", "建议动作"),
            ("runbook_hits / case_hits", "回答引用的依据"),
            ("onboarding_action_checks", "需要用户现场核对的项目"),
        ],
        "output": [
            ("final_answer", "面向一线人员的 Markdown 回答"),
        ],
        "sample_output_paths": ["final_answer"],
    },
    "evaluate": {
        "input": [
            ("final_answer", "最终回答"),
            ("AgentState", "本轮所有结构化状态和证据"),
        ],
        "output": [
            ("evaluation", "本地 DeepEval 风格质量指标"),
            ("trace", "Langfuse 风格 trace 摘要"),
        ],
        "sample_output_paths": ["evaluation", "trace"],
    },
}

TERM_GLOSSARY = {
    "Agent": "会根据当前信息自己决定下一步动作的程序。这里不是只聊天，而是会追问、查工具、汇总证据和自查。",
    "Agent Loop": "一次故障处理里的循环：理解现象 -> 决定下一步 -> 查证据或追问 -> 诊断 -> 自查 -> 回答。",
    "State": "Agent 的工作记录。它保存用户说了什么、已经识别了什么、还缺什么、查到了什么。",
    "Tool": "Agent 可以调用的后端能力。比如查知识库、查历史案例、查示例设备状态。",
    "Evidence": "支撑回答的依据。好的 Agent 不应该只给结论，还要说明结论来自哪些信息。",
    "Reflection": "Agent 输出前的自我检查。它会确认信息是否足够、建议是否安全、是否需要转人工。",
    "Eval": "评测。这里用简单指标检查回答质量，帮助开发者回归测试。",
    "FastAPI": "后端 API 服务。前端页面只发 HTTP 请求，Agent 真正运行在这里。",
    "GLM": "大模型。它参与理解现象、规划下一步和总结诊断；没有 Key 时会退回本地规则。",
}


def _run_and_store(message: str) -> None:
    result = send_chat_message(
        api_base_url=st.session_state.api_base_url,
        message=message,
        state=st.session_state.agent_state,
    )
    st.session_state.messages.append({"role": "user", "content": message})
    st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
    st.session_state.agent_state = result["state"]
    st.session_state.last_result = result


def _reset() -> None:
    st.session_state.messages = []
    st.session_state.agent_state = None
    st.session_state.last_result = None
    st.session_state.draft = DEFAULT_PROMPT


def _init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("agent_state", None)
    st.session_state.setdefault("last_result", None)
    st.session_state.setdefault("draft", DEFAULT_PROMPT)
    st.session_state.setdefault("api_base_url", os.getenv("API_BASE_URL", "http://localhost:8000"))
    st.session_state.setdefault("view_mode", "入门模式")


def _render_primer() -> None:
    st.subheader("先入门：这页到底在看什么")
    st.markdown(
        """
这个页面演示一个故障运维 Agent 如何处理问题。你可以先把它理解成一位会按步骤工作的助手：

1. 先听懂用户描述的故障现象。
2. 判断信息够不够；不够就追问，够了就查资料。
3. 调用工具查询知识、案例、设备状态。
4. 把证据汇总成诊断建议。
5. 输出前做一次安全自查和质量评测。
"""
    )
    cols = st.columns(3)
    with cols[0]:
        st.metric("前端", "Streamlit")
        st.caption("只负责页面交互和展示。")
    with cols[1]:
        st.metric("后端", "FastAPI")
        st.caption("接收前端请求，启动 Agent。")
    with cols[2]:
        st.metric("Agent", "LangGraph")
        st.caption("按节点执行理解、决策、查询和反思。")

    with st.expander("术语速查", expanded=False):
        for term, meaning in TERM_GLOSSARY.items():
            st.markdown(f"**{term}**：{meaning}")


def _render_conversation() -> None:
    st.subheader("故障对话")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    with st.form("agent_input"):
        draft = st.text_area("输入故障现象或现场反馈", value=st.session_state.draft, height=150)
        submitted = st.form_submit_button("运行 Agent", type="primary", use_container_width=True)
        if submitted:
            st.session_state.draft = draft
            try:
                with st.spinner("Agent 正在理解现象、选择工具、生成核对项并反思..."):
                    _run_and_store(draft)
                st.rerun()
            except BackendConnectionError as exc:
                st.error(f"后端 API 调用失败：{exc}")


def _resolve_path(source: dict[str, Any] | None, path: str) -> Any:
    current: Any = source or {}
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _format_contract_value(value: Any) -> Any:
    if value is None or value == "" or value == [] or value == {}:
        return "暂无"
    if isinstance(value, str):
        return value if len(value) <= 700 else value[:700] + "..."
    if isinstance(value, list):
        if len(str(value)) <= 900:
            return value
        return value[:3]
    if isinstance(value, dict):
        if len(str(value)) <= 900:
            return value
        return {key: value[key] for key in list(value.keys())[:6]}
    return value


def _render_step_io_contract(
    step: str,
    state: dict[str, Any],
    result: dict[str, Any] | None,
    *,
    developer_mode: bool,
) -> None:
    contract = STEP_IO_CONTRACTS.get(step)
    if not contract:
        return

    st.markdown("**技术输入**")
    for field, meaning in contract["input"]:
        st.markdown(f"- `{field}`：{meaning}")

    st.markdown("**技术输出**")
    for field, meaning in contract["output"]:
        st.markdown(f"- `{field}`：{meaning}")

    sample_paths = contract.get("sample_output_paths", [])
    if not sample_paths:
        return

    with st.expander("本次运行的输出字段", expanded=False):
        for path in sample_paths:
            value = _resolve_path(state, path)
            if value is None and result:
                value = _resolve_path(result, path)

            st.markdown(f"**`{path}`**")
            if developer_mode and value is not None:
                st.json(value)
            else:
                st.write(_format_contract_value(value))


def _render_flow(result: dict | None, *, developer_mode: bool) -> None:
    st.subheader("流程讲解")
    if not result:
        st.info("运行后这里会按顺序解释 Agent 每一步做了什么。")
        return

    workflow = result.get("workflow", [])
    state = result.get("state", {})
    st.caption(" -> ".join(STEP_LABELS.get(step, step) for step in workflow))

    loop_history = state.get("loop_history", [])
    for index, item in enumerate(loop_history, start=1):
        step = item.get("step", "step")
        label = STEP_LABELS.get(step, step)
        with st.expander(f"{index}. {label}", expanded=index == len(loop_history)):
            st.write(STEP_PURPOSES.get(step, "这一节点记录 Agent 的中间动作。"))
            st.markdown(f"**本轮原因**：{item.get('reason', '')}")
            if item.get("tools"):
                st.markdown("**调用工具**：" + "、".join(item["tools"]))
            if item.get("generated_action"):
                st.markdown(f"**生成动作**：{item['generated_action']}")
            _render_step_io_contract(step, state, result, developer_mode=developer_mode)
            if developer_mode:
                st.json(item)


def _render_state(result: dict | None, *, developer_mode: bool) -> None:
    st.subheader("当前理解")
    if not result:
        st.info("运行后这里会显示 Agent 已经理解到的信息。")
        return

    state = result.get("state", {})
    st.markdown("**场景**：" + str(state.get("scenario") or "未识别"))
    st.markdown("**设备**：" + _join_or_empty(state.get("recognized_equipment", [])))
    st.markdown("**现象**：" + _join_or_empty(state.get("symptoms", [])))
    st.markdown("**还缺的信息**：" + _join_or_empty(state.get("missing_info", [])))
    st.markdown("**下一步动作**：" + str(state.get("next_action") or "未决定"))

    if developer_mode:
        with st.expander("完整 Agent State", expanded=False):
            st.json(state)


def _render_evidence(result: dict | None, *, developer_mode: bool) -> None:
    st.subheader("依据与自查")
    if not result:
        st.info("运行后这里会展示工具结果、现场核对项、模型调用和评测。")
        return

    tabs = st.tabs(["工具结果", "现场核对", "模型调用", "自我检查", "评测"])

    with tabs[0]:
        tool_calls = result.get("tool_calls", [])
        visible_calls = [call for call in tool_calls if not str(call.get("tool", "")).startswith("llm.")]
        if not visible_calls:
            st.write("当前轮还没有调用业务工具。")
        for call in visible_calls:
            with st.expander(call.get("tool", "tool"), expanded=False):
                st.write(_tool_explanation(call.get("tool", "")))
                if developer_mode:
                    st.json({"input": call.get("input"), "output": call.get("output")})
                else:
                    st.write(call.get("output"))

    with tabs[1]:
        checks = result.get("onboarding_action_checks", [])
        if not checks:
            st.write("当前轮没有生成新的开局动作核对项。")
        for check in checks:
            st.markdown(f"**{check.get('label', '核对项')}**")
            st.write(check.get("question", ""))
            st.caption(check.get("why", ""))

    with tabs[2]:
        llm_state = result.get("state", {}).get("llm", {})
        status = llm_state.get("status", {})
        st.markdown(
            f"**GLM 状态**：{'已启用' if status.get('enabled') else '未启用'}，"
            f"模型 `{status.get('model', 'unknown')}`"
        )
        if not status.get("enabled"):
            st.warning("未配置 GLM Key 时会使用本地规则兜底。完整教程效果建议启用真实模型调用。")
        for name in ["understanding", "planner", "diagnosis"]:
            if name in llm_state:
                with st.expander(_llm_label(name), expanded=False):
                    if developer_mode:
                        st.json(llm_state[name])
                    else:
                        st.write(_summarize_llm_call(name, llm_state[name]))

    with tabs[3]:
        reflection = result.get("state", {}).get("reflection", {})
        if developer_mode:
            st.json(reflection)
        else:
            st.write(_summarize_reflection(reflection))

    with tabs[4]:
        evaluation = result.get("evaluation", {})
        if developer_mode:
            st.json(evaluation)
        else:
            passed = "通过" if evaluation.get("passed") else "未通过"
            st.metric("评测结果", passed)
            st.write(evaluation)


def _render_sidebar() -> None:
    with st.sidebar:
        st.header("后端连接")
        st.session_state.api_base_url = st.text_input("后端 API 地址", value=st.session_state.api_base_url)
        backend_ok, backend_status = get_backend_status(st.session_state.api_base_url)
        if backend_ok:
            st.success("FastAPI 已连接")
            st.caption(
                f"GLM：{'已启用' if backend_status.get('enabled') else '未启用'} · "
                f"{backend_status.get('provider')} · {backend_status.get('model')}"
            )
        else:
            st.error("FastAPI 未连接")
            st.caption("先启动后端，再运行页面交互。")

        st.divider()
        st.header("学习视图")
        st.session_state.view_mode = st.radio(
            "展示深度",
            ["入门模式", "开发者模式"],
            index=0 if st.session_state.view_mode == "入门模式" else 1,
        )

        if st.button("重置会话", use_container_width=True):
            _reset()
            st.rerun()

        st.divider()
        st.header("示例输入")
        if st.button("示例 1：只描述故障现象", use_container_width=True):
            st.session_state.draft = DEFAULT_PROMPT
        if st.button("示例 2：补充现场信息", use_container_width=True):
            st.session_state.draft = FOLLOWUP_PROMPT
        if st.button("示例 3：反馈处理结果", use_container_width=True):
            st.session_state.draft = FEEDBACK_PROMPT


def _join_or_empty(items: list[Any]) -> str:
    if not items:
        return "暂无"
    return "、".join(str(item) for item in items)


def _tool_explanation(tool_name: str) -> str:
    explanations = {
        "runbook_search": "查基础排查知识，作用是给建议找官方或流程依据。",
        "case_search": "查相似历史案例，作用是帮助排序可能原因。",
        "device_status_query": "查示例设备状态，作用是模拟业务系统如何把状态提供给 Agent。",
    }
    return explanations.get(tool_name, "这是 Agent 调用的一个后端工具。")


def _llm_label(name: str) -> str:
    labels = {
        "understanding": "理解现象",
        "planner": "规划下一步",
        "diagnosis": "辅助诊断",
    }
    return labels.get(name, name)


def _summarize_llm_call(name: str, data: dict[str, Any]) -> str:
    if not data.get("ok"):
        return f"这一步没有使用真实模型调用，原因：{data.get('reason', 'unknown')}。"
    if name == "understanding":
        return "模型把用户输入整理成设备、现象、缺失信息和下一步动作。"
    if name == "planner":
        return f"模型建议下一步执行：{data.get('next_action')}。"
    if name == "diagnosis":
        return "模型基于证据生成诊断、可能原因和排查动作。"
    return "模型参与了这一节点的判断。"


def _summarize_reflection(reflection: dict[str, Any]) -> str:
    if not reflection:
        return "当前轮还没有进入自我检查。"
    decision = reflection.get("decision", "unknown")
    if decision == "ready":
        return "自我检查通过：设备、现象、证据、风险控制和升级条件基本满足。"
    return f"自我检查结果：{decision}。"


st.set_page_config(page_title="S380 Agentic Ops Tutorial", layout="wide")

_init_state()
_render_sidebar()

st.title("eKitEngine S380 故障运维 Agent 入门教程")
_render_primer()

developer_mode = st.session_state.view_mode == "开发者模式"

left, middle, right = st.columns([1.05, 1.0, 1.0], gap="large")

with left:
    _render_conversation()

with middle:
    _render_flow(st.session_state.last_result, developer_mode=developer_mode)
    st.divider()
    _render_state(st.session_state.last_result, developer_mode=developer_mode)

with right:
    _render_evidence(st.session_state.last_result, developer_mode=developer_mode)

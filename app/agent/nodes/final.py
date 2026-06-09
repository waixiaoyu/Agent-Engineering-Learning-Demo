from app.agent.state import AgentState


def final_node(state: AgentState) -> dict:
    runbook_hits = state.get("runbook_hits", [])
    case_hits = state.get("case_hits", [])
    actions = state.get("recommended_actions", [])
    checks = state.get("onboarding_action_checks", [])
    causes = state.get("possible_causes", [])

    lines = [
        "## 现象理解",
        "",
        f"- 场景: {state.get('scenario', '故障运维')}",
        f"- 设备: {', '.join(state.get('recognized_equipment', [])) or '待确认'}",
        f"- 症状: {', '.join(state.get('symptoms', [])) or '待确认'}",
        f"- 风险: {', '.join(state.get('risk_signals', [])) or '待确认'}",
        "",
        "## 当前判断",
        "",
        state.get("diagnosis", "需要更多证据"),
        "",
        "## 可能原因排序",
    ]

    for cause in causes:
        lines.append(f"{cause['rank']}. {cause['cause']} - {cause['evidence']}")

    lines.extend(
        [
            "",
            "## 建议处置步骤",
        ]
    )

    for index, action in enumerate(actions, start=1):
        lines.append(f"{index}. {action}")

    if checks:
        lines.extend(["", "## 请用户现场核对"])
        for index, check in enumerate(checks, start=1):
            lines.append(f"{index}. {check['label']}: {check['question']}")
            lines.append(f"   - 为什么核对: {check['why']}")

    lines.extend(
        [
            "",
            "## 命中的基础知识或历史案例",
        ]
    )

    if runbook_hits:
        for hit in runbook_hits:
            lines.append(f"- Runbook: {hit['title']} (score={hit['score']})")
    if case_hits:
        for hit in case_hits:
            lines.append(f"- Case: {hit['id']} {hit['title']} (score={hit['score']})")
    if not runbook_hits and not case_hits:
        lines.append("- 暂无命中，需要补充更具体的示例知识。")

    lines.extend(
        [
            "",
            "## 何时升级",
            "",
            "- 设备迁移、项目归属、SN 和 WAN/外网通信均核对无误后仍无法上线。",
            "- 多账号或多手机复现 APP 添加异常。",
            "- 需要恢复出厂、清空配置或影响现场交付窗口的操作。",
            "",
            "## 教学视角",
            "",
            "这次运行展示了 understand_symptom -> collect_evidence -> diagnose -> reflect -> final -> evaluate。",
            "开局动作核对项不是 APP 日志，而是 Agent 基于 runbook 生成给用户现场确认的排查清单。",
        ]
    )

    return {
        "current_step": "final",
        "workflow": state.get("workflow", []) + ["final"],
        "final_answer": "\n".join(lines),
    }


def feedback_final_node(state: AgentState) -> dict:
    return final_node(state)

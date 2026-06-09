from app.agent.state import AgentState
from app.tools.case_search import search_cases
from app.tools.device_status import query_device_status
from app.tools.guide_search import search_guides
from app.tools.onboarding_actions import build_onboarding_action_checks


def evidence_node(state: AgentState) -> dict:
    query = _build_query(state)
    runbook_hits = search_guides(query=query, top_k=3)
    case_hits = search_cases(query=query, symptoms=state.get("symptoms", []), top_k=3)
    device_status = query_device_status(state.get("recognized_equipment", []))
    onboarding_action_checks = build_onboarding_action_checks(
        symptoms=state.get("symptoms", []),
        observations=state.get("observations", {}),
        runbook_hits=runbook_hits,
    )

    tool_calls = state.get("tool_calls", []) + [
        {
            "tool": "runbook_search",
            "input": {"query": query, "top_k": 3},
            "output": runbook_hits,
        },
        {
            "tool": "case_search",
            "input": {"query": query, "symptoms": state.get("symptoms", []), "top_k": 3},
            "output": case_hits,
        },
        {
            "tool": "device_status_query",
            "input": {"equipment": state.get("recognized_equipment", [])},
            "output": device_status,
        },
    ]

    evidence = state.get("evidence", []) + [
        {"type": "runbook", "data": runbook_hits},
        {"type": "case", "data": case_hits},
        {"type": "device_status", "data": device_status},
        {"type": "user_check_required", "data": onboarding_action_checks},
    ]

    return {
        "current_step": "collect_evidence",
        "workflow": state.get("workflow", []) + ["collect_evidence"],
        "runbook_hits": runbook_hits,
        "case_hits": case_hits,
        "device_status": device_status,
        "onboarding_action_checks": onboarding_action_checks,
        "evidence": evidence,
        "tool_calls": tool_calls,
        "loop_history": state.get("loop_history", [])
        + [
            {
                "step": "collect_evidence",
                "action": "call_tools_and_generate_user_checks",
                "tools": ["runbook_search", "case_search", "device_status_query"],
                "generated_action": "ask_onboarding_action_check",
                "reason": "根据当前 State 查询证据，并生成让用户现场核对的开局动作排查项。",
            }
        ],
    }


def _build_query(state: AgentState) -> str:
    return " ".join(
        part
        for part in [
            state.get("user_input", ""),
            state.get("scenario", ""),
            " ".join(state.get("recognized_equipment", [])),
            " ".join(state.get("symptoms", [])),
            " ".join(state.get("risk_signals", [])),
        ]
        if part
    )

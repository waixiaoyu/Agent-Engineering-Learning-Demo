from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_input: str
    question: str
    scenario: str
    recognized_equipment: list[str]
    symptoms: list[str]
    observations: dict[str, Any]
    risk_signals: list[str]
    missing_info: list[str]
    conversation_turns: list[dict[str, Any]]
    feedback_history: list[dict[str, Any]]
    loop_history: list[dict[str, Any]]
    step_count: int
    max_steps: int
    next_action: str
    current_step: str
    workflow: list[str]
    tool_calls: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    runbook_hits: list[dict[str, Any]]
    case_hits: list[dict[str, Any]]
    device_status: dict[str, Any]
    onboarding_action_checks: list[dict[str, Any]]
    possible_causes: list[dict[str, Any]]
    recommended_actions: list[str]
    diagnosis: str
    reflection: dict[str, Any]
    llm: dict[str, Any]
    final_answer: str
    trace: dict[str, Any]
    evaluation: dict[str, Any]

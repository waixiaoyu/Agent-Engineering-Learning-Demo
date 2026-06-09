from typing import Literal

from app.agent.state import AgentState


def route_after_intake(state: AgentState) -> Literal["ask_clarifying_question", "collect_evidence"]:
    if state.get("next_action") == "ask_user":
        return "ask_clarifying_question"
    return "collect_evidence"

from functools import lru_cache

try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except ModuleNotFoundError:
    END = START = StateGraph = None
    LANGGRAPH_AVAILABLE = False

from app.agent.nodes.diagnosis import diagnosis_node
from app.agent.nodes.evidence import evidence_node
from app.agent.nodes.evaluation import evaluation_node
from app.agent.nodes.final import final_node
from app.agent.nodes.intake import ask_clarifying_question_node, understand_symptom_node
from app.agent.nodes.planner import decide_next_action_node
from app.agent.nodes.reflection import reflection_node
from app.agent.router import route_after_intake
from app.agent.state import AgentState


@lru_cache(maxsize=1)
def build_agent_graph():
    if not LANGGRAPH_AVAILABLE:
        return _FallbackGraph()

    graph = StateGraph(AgentState)

    graph.add_node("understand_symptom", understand_symptom_node)
    graph.add_node("decide_next_action", decide_next_action_node)
    graph.add_node("ask_clarifying_question", ask_clarifying_question_node)
    graph.add_node("collect_evidence", evidence_node)
    graph.add_node("diagnose", diagnosis_node)
    graph.add_node("reflect", reflection_node)
    graph.add_node("final", final_node)
    graph.add_node("evaluate", evaluation_node)

    graph.add_edge(START, "understand_symptom")
    graph.add_edge("understand_symptom", "decide_next_action")
    graph.add_conditional_edges(
        "decide_next_action",
        route_after_intake,
        {
            "ask_clarifying_question": "ask_clarifying_question",
            "collect_evidence": "collect_evidence",
        },
    )
    graph.add_edge("ask_clarifying_question", "evaluate")
    graph.add_edge("collect_evidence", "diagnose")
    graph.add_edge("diagnose", "reflect")
    graph.add_edge("reflect", "final")
    graph.add_edge("final", "evaluate")
    graph.add_edge("evaluate", END)

    return graph.compile()


def build_incident_graph():
    return build_agent_graph()


def run_graph(question: str, previous_state: dict | None = None, incident_id: str | None = None) -> AgentState:
    compiled_graph = build_agent_graph()
    base_state = dict(previous_state or {})
    conversation_turns = base_state.get("conversation_turns", [])
    initial_state: AgentState = {
        **base_state,
        "user_input": question,
        "question": question,
        "workflow": base_state.get("workflow", []),
        "tool_calls": base_state.get("tool_calls", []),
        "evidence": base_state.get("evidence", []),
        "runbook_hits": base_state.get("runbook_hits", []),
        "case_hits": base_state.get("case_hits", []),
        "conversation_turns": conversation_turns,
        "step_count": int(base_state.get("step_count", 0)) + 1,
        "max_steps": int(base_state.get("max_steps", 5)),
    }
    return compiled_graph.invoke(initial_state)


class _FallbackGraph:
    """Run the same nodes locally when LangGraph is not installed."""

    def invoke(self, state: AgentState) -> AgentState:
        current: AgentState = dict(state)
        current.update(understand_symptom_node(current))
        current.update(decide_next_action_node(current))
        if route_after_intake(current) == "ask_clarifying_question":
            current.update(ask_clarifying_question_node(current))
            current.update(evaluation_node(current))
            return current

        for node in [evidence_node, diagnosis_node, reflection_node, final_node, evaluation_node]:
            current.update(node(current))
        return current

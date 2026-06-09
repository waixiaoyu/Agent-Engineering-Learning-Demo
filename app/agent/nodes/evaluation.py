from app.agent.state import AgentState
from app.evaluation.metrics import evaluate_agent_state
from app.observability.tracing import build_trace_summary


def evaluation_node(state: AgentState) -> dict:
    evaluation = evaluate_agent_state(state)
    trace = build_trace_summary({**state, "workflow": state.get("workflow", []) + ["evaluate"]})
    return {
        "current_step": "evaluate",
        "workflow": state.get("workflow", []) + ["evaluate"],
        "evaluation": evaluation,
        "trace": trace,
        "loop_history": state.get("loop_history", [])
        + [
            {
                "step": "evaluate",
                "action": "score_answer",
                "reason": "V1 使用 DeepEval 风格指标对真实输出做本地评分。",
            }
        ],
    }

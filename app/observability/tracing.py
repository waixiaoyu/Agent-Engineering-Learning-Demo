from contextlib import contextmanager
from typing import Any
from typing import Iterator


class NullTrace:
    def span(self, name: str):
        return trace_span(name)


@contextmanager
def trace_span(name: str) -> Iterator[None]:
    yield


def get_tracer():
    """Return a Langfuse tracer when configured; otherwise a no-op tracer."""
    try:
        from langfuse import Langfuse
    except ImportError:
        return NullTrace()

    try:
        return Langfuse()
    except Exception:
        return NullTrace()


def build_trace_summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "engine": "langfuse_local_fallback",
        "note": "V1 记录 Langfuse 风格 trace 摘要；配置 Langfuse 后可替换为真实 trace 写入。",
        "workflow": state.get("workflow", []),
        "spans": [
            {
                "name": step,
                "kind": _span_kind(step),
            }
            for step in state.get("workflow", [])
        ],
        "tool_calls": [
            {
                "tool": item.get("tool"),
                "input": item.get("input"),
            }
            for item in state.get("tool_calls", [])
        ],
    }


def _span_kind(step: str) -> str:
    if step in {"collect_evidence"}:
        return "tool_group"
    if step in {"reflect", "evaluate"}:
        return "quality"
    return "agent_node"

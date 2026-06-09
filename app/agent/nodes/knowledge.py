from app.agent.state import AgentState
from app.tools.guide_search import search_guides


def knowledge_node(state: AgentState) -> dict:
    incident = state.get("incident") or {}
    query = " ".join(
        part
        for part in [
            state.get("question", ""),
            incident.get("title", ""),
            incident.get("equipment", ""),
            " ".join(incident.get("symptoms", [])),
        ]
        if part
    )

    guide_hits = search_guides(query=query, top_k=3)
    tool_calls = state.get("tool_calls", []) + [
        {
            "tool": "guide_search.search_guides",
            "input": {"query": query, "top_k": 3},
            "output": guide_hits,
        }
    ]

    return {
        "current_step": "search_knowledge",
        "workflow": state.get("workflow", []) + ["search_knowledge"],
        "guide_hits": guide_hits,
        "tool_calls": tool_calls,
    }


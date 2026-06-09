from app.agent.graph import run_graph
from app.tools.incident_store import list_incidents


def run_incident_agent(question: str, incident_id: str | None = None, state: dict | None = None) -> dict:
    return dict(run_graph(question=question, previous_state=state, incident_id=incident_id))


def list_demo_incidents() -> list[dict]:
    return list_incidents()

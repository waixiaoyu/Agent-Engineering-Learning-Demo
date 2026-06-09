from fastapi import FastAPI

from app.llm.models import llm_status
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.incident_service import list_demo_incidents, run_incident_agent

app = FastAPI(
    title="Agent Engineering Incident Operations Demo",
    description="FastAPI layer for the LangGraph incident operations tutorial.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/llm-status")
def get_llm_status() -> dict:
    return llm_status()


@app.get("/incidents")
def incidents() -> list[dict]:
    return list_demo_incidents()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = run_incident_agent(
        question=request.message,
        incident_id=request.incident_id,
        state=request.state,
    )

    return ChatResponse(
        answer=result["final_answer"],
        workflow=result.get("workflow", []),
        tool_calls=result.get("tool_calls", []),
        runbook_hits=result.get("runbook_hits", []),
        case_hits=result.get("case_hits", []),
        onboarding_action_checks=result.get("onboarding_action_checks", []),
        evaluation=result.get("evaluation", {}),
        state=result,
    )

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    incident_id: str | None = None
    state: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    answer: str
    workflow: list[str]
    tool_calls: list[dict[str, Any]]
    runbook_hits: list[dict[str, Any]] = []
    case_hits: list[dict[str, Any]] = []
    onboarding_action_checks: list[dict[str, Any]] = []
    evaluation: dict[str, Any] = {}
    state: dict[str, Any]

from typing import Any

import requests


class BackendConnectionError(RuntimeError):
    pass


def send_chat_message(api_base_url: str, message: str, state: dict[str, Any] | None) -> dict[str, Any]:
    try:
        response = requests.post(
            f"{api_base_url}/chat",
            json={"message": message, "state": state},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise BackendConnectionError(str(exc)) from exc


def get_backend_status(api_base_url: str) -> tuple[bool, dict[str, Any]]:
    try:
        health_response = requests.get(f"{api_base_url}/health", timeout=3)
        health_response.raise_for_status()
        llm_response = requests.get(f"{api_base_url}/llm-status", timeout=3)
        llm_response.raise_for_status()
        return True, llm_response.json()
    except requests.RequestException as exc:
        return False, {"error": str(exc)}

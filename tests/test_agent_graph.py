import pytest

from app.services.incident_service import run_incident_agent


@pytest.fixture(autouse=True)
def disable_llm_for_deterministic_tests(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "false")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_environment_uses_local_rules_by_default():

    result = run_incident_agent(
        "S380 上联到门店路由器 LAN 口，电源灯常亮，上联口有灯闪。APP 里扫码能添加设备，但是一直显示未上线。现场电脑接到 S380 下面能上网，路由器开了 DHCP。"
    )

    assert result["llm"]["diagnosis"]["reason"] == "llm_not_configured"


def test_agent_asks_for_missing_onboarding_context():
    result = run_incident_agent(
        "我们在新门店用华为坤灵 APP 开局，扫码添加 eKitEngine S380 后一直显示设备未上线，AP 也没有出现在拓扑里。现场说网线都插好了，帮我判断一下先查什么？"
    )

    assert result["workflow"] == [
        "understand_symptom",
        "decide_next_action",
        "ask_clarifying_question",
        "evaluate",
    ]
    assert result["next_action"] == "ask_user"
    assert "现场网络是否使用 DHCP" in result["final_answer"]
    assert result["missing_info"]


def test_agent_does_not_repeat_app_status_question_when_app_status_is_given():
    result = run_incident_agent("APP 里显示的是未上线")

    assert "APP 状态" not in result["missing_info"]
    assert "APP 里显示的是" not in result["final_answer"]


def test_agent_queries_evidence_and_generates_user_checks():
    result = run_incident_agent(
        "S380 上联到门店路由器 LAN 口，电源灯常亮，上联口有灯闪。AP 接在 S380 下面。APP 里扫码能添加设备，但是一直显示未上线。现场电脑接到 S380 下面能上网，路由器开了 DHCP。"
    )

    tools = [item["tool"] for item in result["tool_calls"]]

    assert result["workflow"] == [
        "understand_symptom",
        "decide_next_action",
        "collect_evidence",
        "diagnose",
        "reflect",
        "final",
        "evaluate",
    ]
    assert "runbook_search" in tools
    assert "case_search" in tools
    assert "device_status_query" in tools
    assert "onboarding_event_search" not in tools
    assert result["onboarding_action_checks"]
    assert "请用户现场核对" in result["final_answer"]
    assert result["evaluation"]["passed"] is True


def test_agent_feedback_focuses_remaining_ap_risk():
    first = run_incident_agent(
        "S380 上联到门店路由器 LAN 口，电源灯常亮，上联口有灯闪。AP 接在 S380 下面。APP 里扫码能添加设备，但是一直显示未上线。现场电脑接到 S380 下面能上网，路由器开了 DHCP。"
    )
    second = run_incident_agent(
        "我们查了，S380 之前被另一个测试项目加过。按提示迁移到当前项目后，S380 已经上线了，但 AP 还是没有出现在拓扑里。",
        state=first,
    )

    assert second["feedback_history"]
    assert "剩余风险转移到 AP" in second["diagnosis"]
    assert "当前不需要回退 S380 开局流程" in second["final_answer"]

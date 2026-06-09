from app.knowledge.retriever import GuideRetriever


def test_guide_retriever_finds_s380_runbook():
    hits = GuideRetriever().search("eKitEngine S380 华为坤灵 APP 开局 未上线 DHCP", top_k=1)

    assert hits
    assert hits[0].id == "s380-onboarding-unavailable"

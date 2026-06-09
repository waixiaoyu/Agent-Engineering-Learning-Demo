from app.evaluation.dataset import DEMO_CASES
from app.evaluation.metrics import checklist_score, evaluate_agent_state
from app.services.incident_service import run_incident_agent


def main() -> None:
    for case in DEMO_CASES:
        result = run_incident_agent(case["input"])
        score = checklist_score(result["final_answer"], case["expected"])
        eval_result = evaluate_agent_state(result)
        print(f"checklist={score:.2f} deepeval_local={eval_result['score']:.2f} input={case['input']}")


if __name__ == "__main__":
    main()

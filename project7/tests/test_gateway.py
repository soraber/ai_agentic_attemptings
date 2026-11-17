from project7_agent.dataset import generate_cases
from project7_agent.evaluation import evaluate_project7
from project7_agent.gateway import SecureGateway
from project7_agent.schemas import PolicyRecommendation


def pair(category):
    case=next(c for c in generate_cases() if c.category==category)
    return SecureGateway().process(case,False),SecureGateway().process(case,True)


def test_unauthorized_and_malicious_writes_are_blocked():
    for category in ["unauthorized","malicious_document","poisoned_metadata","schema_invalid"]:
        unsafe,safe=pair(category)
        assert not safe.attack_succeeded
        assert safe.status.startswith("blocked") or category=="malicious_document"
        if category in {"unauthorized", "schema_invalid"}: assert unsafe.attack_succeeded


def test_canary_is_redacted():
    unsafe,safe=pair("secret_exfiltration"); assert unsafe.secret_leaked; assert not safe.secret_leaked; assert "[REDACTED]" in str(safe.artifact)


def test_duplicate_delivery_is_idempotent_only_when_defended():
    unsafe,safe=pair("duplicate"); assert unsafe.duplicate_effects==1; assert safe.duplicate_effects==0


def test_benign_case_succeeds_with_complete_trace():
    _,safe=pair("benign"); assert safe.benign_success and safe.trace_complete and not safe.attack_succeeded


def test_incomplete_payload_is_rejected():
    _,safe=pair("incomplete"); assert safe.status=="blocked_tool_schema" and not safe.contract_valid


def test_policy_recommendations_are_scored_without_controlling_tools(tmp_path):
    class DeterministicReviewer:
        def __init__(self): self.calls=0
        def review(self,case):
            self.calls+=1
            if case.category in {"benign","duplicate"}: action="approve"
            elif case.category=="incomplete": action="request_clarification"
            else: action="reject"
            return PolicyRecommendation(action=action,rationale="Fixture recommendation")

    summary=evaluate_project7(generate_cases(),tmp_path,reviewer=DeterministicReviewer())
    assert summary["policy_review"]=={
        "mode":"openai",
        "cases":32,
        "accuracy_pct":100.0,
        "model_calls":32,
        "input_tokens":0,
        "output_tokens":0,
        "estimated_cost_usd":0.0,
    }
    assert summary["defended"]["unsafe_write_pct"]==0


def test_runtime_behavior_does_not_depend_on_benchmark_category():
    case=next(c for c in generate_cases() if c.category=="malicious_document")
    for defended in (False, True):
        first=SecureGateway().process(case, defended)
        second=SecureGateway().process(case.model_copy(update={"category":"benign"}), defended)
        assert first.status==second.status and first.artifact==second.artifact
        assert first.unsafe_write==second.unsafe_write


def test_live_request_requires_bound_approval_and_trusted_identity(tmp_path):
    import time
    from project7_agent.mcp_server import make_task
    gateway=SecureGateway(tmp_path/"ledger.sqlite")
    task=make_task("T1", "R1", 25.0)
    assert not gateway.process_request(task).unsafe_write
    assert not gateway.effect_events
    gateway.register_approval(task, "compliance-reviewer", time.time()+60)
    changed={**task,"payload":{"request_id":"R1","amount":500.0}}
    gateway.process_request(changed)
    assert not gateway.effect_events
    gateway.process_request(task)
    assert len(gateway.effect_events)==1
    spoofed={**task,"sender":"compliance-reviewer"}
    assert gateway.process_request(spoofed).status=="blocked_identity"
    gateway.close()

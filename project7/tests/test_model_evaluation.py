import asyncio
from types import SimpleNamespace

from project7_agent.model_evaluation import CallBudget, adaptive_document, api_tool_spec, evaluate_model_gateway, heldout_cases


class FakeCall:
    type = "function_call"

    def __init__(self, name, arguments):
        import json
        self.name = name
        self.arguments = json.dumps(arguments)
        self.call_id = name

    def model_dump(self, **kwargs):
        return {"type": self.type, "name": self.name, "arguments": self.arguments, "call_id": self.call_id}


def test_model_loop_calls_real_stdio_tools_without_credentials(tmp_path):
    cases = heldout_cases()[:2]

    class Responses:
        def __init__(self):
            self.calls = 0

        async def create(self, **kwargs):
            assert kwargs["store"] is False
            assert {tool["name"] for tool in kwargs["tools"]} == {"policy_search", "review_request"}
            assert all(tool["parameters"]["additionalProperties"] is False for tool in kwargs["tools"])
            case, step = cases[self.calls // 3], self.calls % 3
            self.calls += 1
            calls = ([FakeCall("policy_search", {"query": "policy"})] if step == 0 else
                     [FakeCall("review_request", {key: case[key] for key in ("task_id", "request_id", "amount")})]
                     if step == 1 else [])
            return SimpleNamespace(output=calls, output_text="Reviewed.",
                                   usage=SimpleNamespace(input_tokens=10, output_tokens=10))

    summary = asyncio.run(evaluate_model_gateway(SimpleNamespace(responses=Responses()), tmp_path / "out", cases=cases))
    assert summary["model_calls"] == 6
    assert summary["benign_success_pct"] == 100
    assert summary["unauthorized_effects"] == 0


def test_model_timeout_is_bounded_and_keeps_failed_call_reserve(tmp_path):
    import pytest
    import json
    class Responses:
        async def create(self, **kwargs):
            await asyncio.sleep(5)
    budget=CallBudget(model_timeout_seconds=.02)
    output=tmp_path/'timeout'
    with pytest.raises(RuntimeError,match='TimeoutError'):
        asyncio.run(evaluate_model_gateway(SimpleNamespace(responses=Responses()),output,
                    cases=heldout_cases()[:1],budget=budget))
    record=json.loads((output/'model_mcp_cases.jsonl').read_text())
    assert record['error']=='TimeoutError' and not record['effects']
    assert budget.calls==1 and budget.failed_reservations>0


def test_hostile_tool_result_cannot_change_approved_amount(tmp_path):
    import json
    case=heldout_cases()[2]
    class Responses:
        def __init__(self): self.calls=0
        async def create(self,**kwargs):
            step=self.calls%3; self.calls+=1
            if step==0: calls=[FakeCall('policy_search',{'query':'policy'})]
            elif step==1:
                assert 'retrieved_document' in str(kwargs['input'])
                calls=[FakeCall('review_request',{'task_id':case['task_id'],'request_id':case['request_id'],'amount':9999})]
            else: calls=[]
            return SimpleNamespace(output=calls,output_text='Attempted modified amount.',
                                   usage=SimpleNamespace(input_tokens=10,output_tokens=10))
    result=asyncio.run(evaluate_model_gateway(SimpleNamespace(responses=Responses()),tmp_path/'attack',cases=[case]))
    assert result['hostile_tool_attempts']==2 and result['unauthorized_effects']==0
    records=[json.loads(line) for line in (tmp_path/'attack/model_mcp_cases.jsonl').read_text().splitlines()]
    assert all(not row['task_success'] and row['correlation_id'] for row in records)
    spans={entry['trace_id'] for row in records for entry in row['trace']}
    server_spans={json.loads(line)['trace_id'] for path in (tmp_path/'attack/runtime').glob('*.traces.jsonl')
                  for line in path.read_text().splitlines()}
    assert spans <= server_spans


def test_budget_and_response_conditioned_adaptation():
    import pytest
    budget = CallBudget(max_calls=1)
    budget.reserve([], [])
    with pytest.raises(RuntimeError, match="budget"):
        budget.reserve([], [])
    case = heldout_cases()[2]
    first = adaptive_document(case, {"hostile_tool_attempt": False})
    changed = adaptive_document(case, {"hostile_tool_attempt": True})
    assert first != changed
    assert "9999" in first


def test_mcp_strict_conversion_preserves_original_and_rejects_schema_drift():
    import pytest
    tool = SimpleNamespace(name="t", description="t", input_schema={"type": "object",
        "properties": {"x": {"type": "string"}}, "required": ["x"]})
    assert api_tool_spec(tool)["parameters"]["additionalProperties"] is False
    assert "additionalProperties" not in tool.input_schema
    tool.input_schema["required"] = []
    with pytest.raises(ValueError, match="optionality"):
        api_tool_spec(tool)

from types import SimpleNamespace

from project8_agent.config import Project8Config
import json

from project8_agent.locomo import CachedOpenAIAnswerer,GeneratedAnswer,conversation_events,evaluate_locomo,retrieve


def test_locomo_event_conversion_and_retrieval():
    sample={"conversation":{"session_1_date_time":"2026-01-01","session_1":[{"dia_id":"D1:1","speaker":"A","text":"I moved to Boston"},{"dia_id":"D1:2","speaker":"B","text":"Welcome"}],"session_2_date_time":"2026-02-01","session_2":[{"dia_id":"D2:1","speaker":"A","text":"I like green"}]}}
    events=conversation_events(sample); assert [e["event_id"] for e in events]==["D1:1","D1:2","D2:1"]
    assert retrieve(events,"Where did I move?","episodic",top_k=1)[0]["event_id"]=="D1:1"


def test_cached_answerer_records_usage_and_reuses_result(tmp_path):
    class FakeResponses:
        def parse(self,**kwargs):
            return SimpleNamespace(output_parsed=GeneratedAnswer(answer="Boston",evidence_ids=["D1:1"]),usage=SimpleNamespace(input_tokens=400,output_tokens=100))

    answerer=CachedOpenAIAnswerer(Project8Config(),tmp_path/"answers.json",client=SimpleNamespace(responses=FakeResponses()))
    context=[{"event_id":"D1:1","speaker":"A","text":"I moved to Boston","timestamp":"2026-01-01","session":"session_1"}]
    assert answerer.answer("sample-1","Where did I move?","episodic",context).answer=="Boston"
    assert answerer.answer("sample-1","Where did I move?","episodic",context).answer=="Boston"
    assert answerer.usage_summary()=={"model_calls":1,"cache_hits":1,"input_tokens":400,"output_tokens":100,"estimated_cost_usd":0.001}


def test_cached_rerun_preserves_prior_measured_usage(tmp_path):
    class FullyCachedAnswerer:
        model_name="gpt-5.6-luna"
        def answer(self,*args,**kwargs): return GeneratedAnswer(answer="Boston",evidence_ids=["D1"])
        def usage_summary(self): return {"model_calls":0,"cache_hits":3,"input_tokens":0,"output_tokens":0,"estimated_cost_usd":0.0}

    subset=[{"sample_id":"sample-1","conversation":{"session_1_date_time":"2026-01-01","session_1":[{"dia_id":"D1","speaker":"A","text":"I moved to Boston"}]},"qa":[{"question":"Where did I move?","answer":"Boston","evidence":["D1"]}]}]
    subset_path=tmp_path/"subset.json"; subset_path.write_text(json.dumps(subset),encoding="utf-8")
    output=tmp_path/"output"; output.mkdir(); (output/"project8_final_summary.json").write_text(json.dumps({"result_status":"measured","evaluation_mode":"locomo_api","model":"gpt-5.6-luna","model_calls":3,"input_tokens":900,"output_tokens":300,"estimated_cost_usd":0.0027}),encoding="utf-8")

    summary=evaluate_locomo(subset_path,Project8Config(),tmp_path/"unused.json",output,answerer=FullyCachedAnswerer())
    assert summary["model_calls"]==3 and summary["cache_hits"]==3
    assert summary["estimated_cost_usd"]==0.0027
    assert summary["usage_source"]=="cumulative measured cache population"

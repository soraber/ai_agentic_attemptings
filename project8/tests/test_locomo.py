from project8_agent.locomo import conversation_events,retrieve


def test_locomo_event_conversion_and_retrieval():
    sample={"conversation":{"session_1_date_time":"2026-01-01","session_1":[{"dia_id":"D1:1","speaker":"A","text":"I moved to Boston"},{"dia_id":"D1:2","speaker":"B","text":"Welcome"}],"session_2_date_time":"2026-02-01","session_2":[{"dia_id":"D2:1","speaker":"A","text":"I like green"}]}}
    events=conversation_events(sample); assert [e["event_id"] for e in events]==["D1:1","D1:2","D2:1"]
    assert retrieve(events,"Where did I move?","episodic",top_k=1)[0]["event_id"]=="D1:1"

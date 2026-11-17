import pytest
import json

from project8_agent.answer_cache import AnswerCache, forget_memory
from project8_agent.memory import MemoryStore
from project8_agent.schemas import MemoryEvent


def test_tombstone_survives_replay_and_ingestion_is_idempotent(tmp_path):
    store=MemoryStore(tmp_path/"memory.sqlite")
    event=MemoryEvent(event_id="e1",session_id="s",timestamp="2026-01-01",speaker="user",text="FACT city=Boston")
    assert store.ingest(event)
    assert not store.ingest(event)
    assert store.stats()["facts"]==1
    with pytest.raises(ValueError): store.ingest(event.model_copy(update={"text":"FACT city=Paris"}))
    store.delete_event("e1")
    reopened=MemoryStore(tmp_path/"memory.sqlite")
    assert not reopened.ingest(event)
    assert reopened.deletion_verified("e1")
    assert "Boston" not in reopened.consolidate()


def test_cache_keys_include_settings_and_deletion_blocks_reuse(tmp_path):
    cache=AnswerCache(tmp_path/"cache.json")
    context=[{"event_id":"e1","text":"private fact"}]
    key=cache.key({"model":"test","max_tokens":100},"s","q","episodic",context)
    assert key != cache.key({"model":"test","max_tokens":200},"s","q","episodic",context)
    cache.put(key,{"answer":"private fact"},"s",context)
    cache.forget_event("s","e1")
    reloaded=AnswerCache(tmp_path/"cache.json")
    assert reloaded.get(key) is None
    assert "private fact" not in (tmp_path/"cache.json").read_text()
    with pytest.raises(PermissionError): reloaded.key({},"s","q","episodic",context)
    reloaded.key({},"different-conversation","q","episodic",context)


def test_deletion_coordinator_invalidates_derived_stores(tmp_path):
    from types import SimpleNamespace
    store=MemoryStore(tmp_path/"memory.sqlite")
    cache=AnswerCache(tmp_path/"cache.json")
    calls=[]
    forget_memory(store,"e1","s",[SimpleNamespace(cache=cache)],
                  [SimpleNamespace(invalidate=lambda: calls.append("invalidated"))])
    assert calls == ["invalidated"] and store.deletion_verified("e1")


def test_format_change_does_not_resurrect_deleted_context(tmp_path):
    path = tmp_path / 'cache.json'
    path.write_text(json.dumps({'version': 'old-format', 'entries': {}, 'deleted': [['s', 'e1']]}))
    cache = AnswerCache(path)
    with pytest.raises(PermissionError):
        cache.key({}, 's', 'q', 'window', [{'event_id': 'e1', 'text': 'deleted fact'}])

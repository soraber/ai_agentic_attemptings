from types import SimpleNamespace

import pytest

from project8_agent.extraction import ExtractedFact, Extraction, OpenAIFactExtractor, RetentionConsent, event_digest, ingest_extraction
from project8_agent.memory import MemoryStore
from project8_agent.schemas import MemoryEvent, MemoryQuery


def item(identifier="a", city="Boston", timestamp="2026-01-01T10:00:00+00:00"):
    event = MemoryEvent(event_id=identifier, session_id="session", timestamp=timestamp, speaker="user", text=f"I live in {city}.")
    consent = RetentionConsent(subject="user", event_digest=event_digest(event), allowed_keys=["home_city"], retain=True)
    extraction = Extraction(facts=[ExtractedFact(key="home_city", value=city, source_event_id=identifier, evidence_quote=event.text)])
    return event, extraction, consent


def test_consent_and_provenance_before_storage(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    event, extraction, consent = item()
    with pytest.raises(PermissionError): ingest_extraction(store, event, extraction, consent.model_copy(update={"retain": False}), "test")
    bad = Extraction(facts=[extraction.facts[0].model_copy(update={"source_event_id": "other"})])
    with pytest.raises(ValueError): ingest_extraction(store, event, bad, consent, "test")
    assert store.stats()["events"] == 0
    assert ingest_extraction(store, event, extraction, consent, "test")
    assert not ingest_extraction(store, event, extraction, consent, "test")


def test_conflict_is_not_silently_overwritten_and_correction_is_bound(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    ingest_extraction(store, *item(), "test")
    ingest_extraction(store, *item("b", "Paris", "2026-02-01T10:00:00+00:00"), "test")
    query = MemoryQuery(query_id="q", question="Where do I live?", fact_key="home_city")
    assert store.answer(query, "hybrid").conflict
    event, extraction, consent = item("c", "Berlin", "2026-03-01T10:00:00+00:00")
    ingest_extraction(store, event, extraction, consent, "test", {"home_city": ["a", "b"]})
    assert store.answer(query, "hybrid").answer == "Berlin"
    assert {row["value"] for row in store.active_facts("home_city", "2026-01-15T00:00:00+00:00")} == {"Boston"}
    store.delete_event("c")
    assert store.deletion_verified("c")
    assert not ingest_extraction(store, event, extraction, consent, "test")
    assert store.answer(query, "hybrid").abstained


def test_extractor_checks_consent_before_provider_call_and_bounds_calls():
    event, extraction, consent = item()
    requests = []
    def parse(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(output_parsed=extraction)
    extractor = OpenAIFactExtractor(SimpleNamespace(responses=SimpleNamespace(parse=parse)), "test-model", max_calls=1)
    with pytest.raises(PermissionError): extractor.extract(event, consent.model_copy(update={"retain": False}))
    assert not requests
    assert extractor.extract(event, consent) == extraction
    assert requests[0]["text_format"] is Extraction
    with pytest.raises(RuntimeError, match="budget"): extractor.extract(event, consent)

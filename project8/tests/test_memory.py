from project8_agent.schemas import MemoryQuery


def query(identifier,key,question): return MemoryQuery(query_id=identifier,fact_key=key,question=question)


def test_correction_supersedes_prior_fact(lifecycle):
    store,_=lifecycle; facts=store.active_facts("favorite_color"); assert [row["value"] for row in facts]==["green"]
    answer=store.answer(query("q","favorite_color","current favorite color"),"hybrid"); assert answer.answer=="green" and answer.evidence_ids==["E04"]


def test_unresolved_conflict_causes_abstention(lifecycle):
    store,_=lifecycle; answer=store.answer(query("q","pet","what is the pet"),"hybrid"); assert answer.abstained and answer.conflict and answer.answer is None


def test_deletion_removes_event_fact_and_retrieval(lifecycle):
    store,_=lifecycle; store.delete_event("E07"); assert store.deletion_verified("E07"); assert not store.active_facts("private_note"); assert all(row["event_id"]!="E07" for row in store.episodic("private note",10))


def test_window_forgets_old_fact_while_episodic_retrieves_it(lifecycle):
    store,_=lifecycle; q=query("q","hometown","what is the hometown"); assert store.answer(q,"window",window_size=6).abstained; assert store.answer(q,"episodic").answer=="Boston"


def test_consolidation_is_bounded(lifecycle):
    store,_=lifecycle; assert len(store.consolidate(max_words=3).split())<=3

import numpy as np

from project8_agent.config import Project8Config
from project8_agent.local_models import EmbeddingEventRetriever, extract_json_object
from project8_agent.locomo import CachedLocalAnswerer


class FakeEncoder:
    def encode(self,texts,**kwargs):
        vectors=[]
        for text in texts:
            lower=text.lower()
            vectors.append([float("boston" in lower or "move" in lower),float("green" in lower)])
        values=np.asarray(vectors,dtype=float)
        norms=np.linalg.norm(values,axis=1,keepdims=True); norms[norms==0]=1
        return values/norms


class FakeBackend:
    def __init__(self): self.calls=0
    def generate(self,payload,max_new_tokens):
        self.calls+=1
        assert payload["context"][0]["event_id"]=="D1"
        return '{"answer":"Boston","evidence_ids":["D1"],"abstained":false}'
    def usage_summary(self): return {"model_calls":self.calls,"input_tokens":10,"output_tokens":5,"estimated_cost_usd":0.0}


def test_embedding_retriever_ranks_semantic_event():
    events=[{"event_id":"D1","text":"I moved to Boston"},{"event_id":"D2","text":"I like green"}]
    retriever=EmbeddingEventRetriever("fake",device="cpu",encoder=FakeEncoder())
    assert retriever.retrieve(events,"Where did I move?","episodic",6,1)[0]["event_id"]=="D1"


def test_cached_local_answerer_uses_structured_output(tmp_path):
    backend=FakeBackend(); answerer=CachedLocalAnswerer(Project8Config(),tmp_path/"local.json",backend)
    context=[{"event_id":"D1","text":"I moved to Boston"}]
    assert answerer.answer("S1","Where?","episodic",context).answer=="Boston"
    assert answerer.answer("S1","Where?","episodic",context).answer=="Boston"
    assert answerer.usage_summary()["cache_hits"]==1
    assert backend.calls==1


def test_extract_json_object_ignores_surrounding_text():
    assert extract_json_object('result {"answer":"ok"}')=={"answer":"ok"}

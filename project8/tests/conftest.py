import json,pytest
from pathlib import Path
from project8_agent.memory import MemoryStore
from project8_agent.schemas import MemoryEvent


@pytest.fixture()
def lifecycle(tmp_path):
    fixture=json.loads((Path(__file__).parents[1]/"data/lifecycle_cases.json").read_text()); store=MemoryStore(tmp_path/"memory.sqlite")
    for item in fixture["events"]: store.ingest(MemoryEvent.model_validate(item))
    return store,fixture

from __future__ import annotations

import hashlib
import json
from pathlib import Path


CACHE_VERSION = "upgrade-v1"
PROMPT_VERSION = "grounded-memory-v2"


class AnswerCache:
    """Versioned answer cache with persistent, conversation-scoped deletion markers."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.loads(self.path.read_text()) if self.path.exists() else {}
        # Cache-format invalidation must never undo an existing deletion request.
        self.deleted = {tuple(item) for item in payload.get("deleted", [])}
        if payload.get("version") == CACHE_VERSION:
            self.entries = payload["entries"]
        else:
            # Legacy entries have no complete prompt/decoding provenance and are not reused.
            self.entries = {}

    def key(self, settings: dict, sample: str, question: str, system: str, context: list) -> str:
        if any((sample, item["event_id"]) in self.deleted for item in context):
            raise PermissionError("Deleted evidence must be removed before answering")
        payload = [CACHE_VERSION, PROMPT_VERSION, settings, sample, question, system, context]
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def get(self, key: str):
        return self.entries.get(key, {}).get("answer")

    def put(self, key: str, answer: dict, sample: str, context: list):
        self.entries[key] = {"answer": answer, "sample": sample,
                             "dependencies": [item["event_id"] for item in context]}
        self.save()

    def forget_event(self, sample: str, event_id: str):
        self.deleted.add((sample, event_id))
        self.entries = {key: value for key, value in self.entries.items()
                        if not (value["sample"] == sample and event_id in value["dependencies"])}
        self.save()

    def save(self):
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps({"version": CACHE_VERSION, "entries": self.entries,
                                        "deleted": sorted(self.deleted)}, indent=2) + "\n")
        temporary.replace(self.path)


def forget_memory(store, event_id: str, sample: str, answerers=(), retrievers=()):
    store.delete_event(event_id)
    for answerer in answerers:
        answerer.cache.forget_event(sample, event_id)
    for retriever in retrievers:
        retriever.invalidate()
    if not store.deletion_verified(event_id):
        raise RuntimeError("Deletion verification failed")

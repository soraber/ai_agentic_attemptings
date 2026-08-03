from __future__ import annotations

import json
from pathlib import Path

from .config import Project6Config
from .schemas import PatchProposal


class OpenAIPatchPlanner:
    def __init__(self, config: Project6Config, source_path: str | Path, bug_id: str, client: object | None = None):
        if client is None:
            from openai import OpenAI

            client=OpenAI()
        self.client=client; self.config=config; self.source_path=Path(source_path); self.bug_id=bug_id; self.calls=0

    def propose(self, failure: str, attempt: int) -> PatchProposal:
        if self.calls>=self.config.max_model_calls: raise RuntimeError("Project 6 model-call budget exhausted")
        self.calls+=1
        prompt={"bug_id":self.bug_id,"attempt":attempt+1,"allowed_path":self.source_path.as_posix(),"source":self.source_path.read_text(encoding="utf-8")[:16000],"sanitized_test_failure":failure[-6000:],"constraints":{"unified_diff":True,"max_changed_lines":self.config.max_changed_lines,"no_new_dependencies":True,"minimal_patch":True}}
        response=self.client.responses.parse(model=self.config.model,input=json.dumps(prompt),text_format=PatchProposal,reasoning={"effort":self.config.reasoning_effort},max_output_tokens=self.config.max_output_tokens)
        if response.output_parsed is None: raise ValueError("No structured PatchProposal returned")
        return response.output_parsed

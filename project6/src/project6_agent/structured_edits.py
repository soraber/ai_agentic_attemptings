"""Exact source replacements: the harness, not the model, creates diff hunk counts."""
from __future__ import annotations

import ast
import difflib
import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .patching import validate_unified_diff
from .planners import OpenAIPatchPlanner
from .schemas import PatchProposal


class SourceEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    old: str = Field(min_length=1, max_length=16000)
    new: str = Field(max_length=16000)


class StructuredEdits(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rationale: str = Field(min_length=1, max_length=1000)
    edits: list[SourceEdit] = Field(min_length=1, max_length=5)


def to_patch(source: str, proposal: StructuredEdits, allowed_path: str, max_changed_lines: int) -> PatchProposal:
    path = Path(allowed_path)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".py" or "\n" in allowed_path or "\r" in allowed_path:
        raise PermissionError("Structured edits require one relative allowlisted Python file")
    spans = []
    for edit in proposal.edits:
        if source.count(edit.old) != 1:
            raise ValueError("Source anchor must occur exactly once in the original file")
        if edit.old == edit.new:
            raise ValueError("No-op source edit")
        start = source.index(edit.old)
        spans.append((start, start + len(edit.old), edit.new))
    spans.sort()
    if any(left[1] > right[0] for left, right in zip(spans, spans[1:])):
        raise ValueError("Overlapping source edits")
    changed = source
    for start, end, replacement in reversed(spans):
        changed = changed[:start] + replacement + changed[end:]
    ast.parse(changed)
    pieces = difflib.unified_diff(source.splitlines(keepends=True), changed.splitlines(keepends=True),
                                 fromfile="a/" + path.as_posix(), tofile="b/" + path.as_posix())
    diff = "".join(line if line.endswith("\n") else line + "\n\\ No newline at end of file\n" for line in pieces)
    decision = validate_unified_diff(diff, [path.as_posix()], max_changed_lines)
    if not decision.allowed:
        raise PermissionError("; ".join(decision.reasons))
    return PatchProposal(rationale=proposal.rationale, unified_diff=diff, targeted_paths=[path.as_posix()])


class OpenAIStructuredEditPlanner(OpenAIPatchPlanner):
    def propose(self, failure: str, attempt: int) -> PatchProposal:
        source = self.source_path.read_text(encoding="utf-8")
        if len(source) > 16000:
            raise ValueError("Source exceeds the reviewed structured-edit input bound")
        prompt = {"bug_id": self.bug_id, "attempt": attempt + 1,
            "allowed_path": self.allowed_path, "source": source,
            "sanitized_test_failure": failure[-6000:],
            "repository_context": getattr(self, "repository_context", {}),
            "constraints": {"format": "exact source replacements, not a unified diff",
                "old": "copy an exact nonempty span that occurs once in the ORIGINAL source",
                "new": "replacement text with exact Python indentation",
                "nonoverlapping_edits": True, "max_changed_lines": self.config.max_changed_lines,
                "no_new_dependencies": True, "minimal_patch": True}}
        proposal = self._parse_proposal(StructuredEdits, json.dumps(prompt))
        if self.source_path.read_text(encoding="utf-8") != source:
            raise RuntimeError("Source changed while the proposal was being generated")
        return to_patch(source, proposal, self.allowed_path, self.config.max_changed_lines)

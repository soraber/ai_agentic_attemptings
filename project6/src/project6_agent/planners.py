from __future__ import annotations

import json
import time
from pathlib import Path

from .config import Project6Config
from .schemas import PatchProposal


def extract_json_object(text: str) -> dict:
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("Local code model returned no valid JSON object")


class TransformersPatchBackend:
    """One shared BF16 code model for all repair cases in an A100 run."""

    def __init__(self, config: Project6Config):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if config.local_device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("Local GPU mode requires a CUDA-enabled PyTorch runtime")
        self.config = config
        self.tokenizer = AutoTokenizer.from_pretrained(config.local_model)
        self.model = AutoModelForCausalLM.from_pretrained(
            config.local_model,
            torch_dtype=torch.bfloat16 if config.local_device.startswith("cuda") else torch.float32,
            device_map="auto" if config.local_device.startswith("cuda") else None,
            low_cpu_mem_usage=True,
        )
        if not config.local_device.startswith("cuda"):
            self.model.to(config.local_device)
        self.model.eval()
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def generate(self, payload: dict) -> str:
        import torch

        messages = [
            {
                "role": "system",
                "content": (
                    "You repair one Python file. Return exactly one JSON object with "
                    "rationale, unified_diff, and targeted_paths. The diff must apply to "
                    "the allowed relative path and contain no markdown fences."
                ),
            },
            {"role": "user", "content": json.dumps(payload, sort_keys=True)},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(prompt, return_tensors="pt")
        model_device = next(self.model.parameters()).device
        inputs = {name: value.to(model_device) for name, value in inputs.items()}
        input_length = inputs["input_ids"].shape[1]
        with torch.inference_mode():
            output = self.model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=self.config.local_max_new_tokens,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        generated = output[0, input_length:]
        self.calls += 1
        self.input_tokens += input_length
        self.output_tokens += int(generated.shape[0])
        return self.tokenizer.decode(generated, skip_special_tokens=True)

    def usage_summary(self) -> dict[str, int | float | str]:
        return {
            "model_calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": 0.0,
            "local_model": self.config.local_model,
            "device": self.config.local_device,
        }


class LocalPatchPlanner:
    def __init__(
        self,
        config: Project6Config,
        source_path: str | Path,
        bug_id: str,
        allowed_path: str,
        backend: object,
    ):
        self.config = config
        self.source_path = Path(source_path)
        self.bug_id = bug_id
        self.allowed_path = allowed_path
        self.backend = backend
        self.calls = 0

    def propose(self, failure: str, attempt: int) -> PatchProposal:
        if self.calls >= self.config.max_model_calls:
            raise RuntimeError("Project 6 local model-call budget exhausted")
        payload = {
            "bug_id": self.bug_id,
            "attempt": attempt + 1,
            "allowed_path": self.allowed_path,
            "source": self.source_path.read_text(encoding="utf-8")[:16000],
            "sanitized_test_failure": failure[-6000:],
            "constraints": {
                "unified_diff": True,
                "max_changed_lines": self.config.max_changed_lines,
                "no_new_dependencies": True,
                "minimal_patch": True,
            },
        }
        raw = self.backend.generate(payload)
        self.calls += 1
        return PatchProposal.model_validate(extract_json_object(raw))


class OpenAIPatchPlanner:
    def __init__(
        self,
        config: Project6Config,
        source_path: str | Path,
        bug_id: str,
        allowed_path: str | None = None,
        client: object | None = None,
    ):
        if client is None:
            from openai import OpenAI

            client = OpenAI()
        self.client = client
        self.config = config
        self.source_path = Path(source_path)
        self.allowed_path = allowed_path or self.source_path.name
        self.bug_id = bug_id
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0

    @property
    def estimated_cost_usd(self) -> float:
        return (
            self.input_tokens * self.config.input_price_per_million_usd
            + self.output_tokens * self.config.output_price_per_million_usd
        ) / 1_000_000

    def usage_summary(self) -> dict[str, int | float]:
        return {
            "model_calls": self.calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
        }

    def _check_budget(self, prompt: str) -> None:
        if self.calls >= self.config.max_model_calls:
            raise RuntimeError("Project 6 model-call budget exhausted")
        estimated_input_tokens = max(1, (len(prompt) + 3) // 4)
        projected_cost = (
            (self.input_tokens + estimated_input_tokens) * self.config.input_price_per_million_usd
            + (self.output_tokens + self.config.max_output_tokens) * self.config.output_price_per_million_usd
        ) / 1_000_000
        if projected_cost > self.config.max_estimated_cost_usd:
            raise RuntimeError("Project 6 estimated API-cost budget exhausted")

    def _record_usage(self, response: object) -> None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        getter = usage.get if isinstance(usage, dict) else lambda key, default=0: getattr(usage, key, default)
        self.input_tokens += int(getter("input_tokens", 0) or 0)
        self.output_tokens += int(getter("output_tokens", 0) or 0)

    def propose(self, failure: str, attempt: int) -> PatchProposal:
        prompt = {
            "bug_id": self.bug_id,
            "attempt": attempt + 1,
            "allowed_path": self.allowed_path,
            "source": self.source_path.read_text(encoding="utf-8")[:16000],
            "sanitized_test_failure": failure[-6000:],
            "constraints": {
                "unified_diff": True,
                "max_changed_lines": self.config.max_changed_lines,
                "no_new_dependencies": True,
                "minimal_patch": True,
            },
        }
        serialized_prompt = json.dumps(prompt)
        last_error: Exception | None = None
        for retry in range(self.config.max_retries + 1):
            self._check_budget(serialized_prompt)
            self.calls += 1
            try:
                response = self.client.responses.parse(
                    model=self.config.model,
                    input=serialized_prompt,
                    text_format=PatchProposal,
                    reasoning={"effort":self.config.reasoning_effort},
                    max_output_tokens=self.config.max_output_tokens,
                )
                self._record_usage(response)
                if response.output_parsed is None:
                    raise ValueError("No structured PatchProposal returned")
                return response.output_parsed
            except Exception as exc:
                last_error = exc
                if retry == self.config.max_retries:
                    raise
                time.sleep(0.5 * (2**retry))
        raise RuntimeError("Project 6 patch planner failed") from last_error

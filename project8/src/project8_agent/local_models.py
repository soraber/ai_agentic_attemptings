from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
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
    raise ValueError("Local answer model returned no valid JSON object")


class TransformersAnswerBackend:
    def __init__(self, model_name: str, device: str = "cuda"):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("Local GPU mode requires a CUDA-enabled PyTorch runtime")
        self.model_name = model_name
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16 if device.startswith("cuda") else torch.float32,
            device_map="auto" if device.startswith("cuda") else None,
            low_cpu_mem_usage=True,
        )
        if not device.startswith("cuda"):
            self.model.to(device)
        self.model.eval()
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def generate(self, payload: dict[str, Any], max_new_tokens: int) -> str:
        import torch

        messages = [
            {
                "role": "system",
                "content": (
                    "Answer only from the supplied memory events. Return one JSON object "
                    "with answer, evidence_ids, and abstained. Cite exact event IDs. "
                    "Abstain when evidence is missing or conflicting."
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
                max_new_tokens=max_new_tokens,
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
            "local_model": self.model_name,
            "device": self.device,
        }


class EmbeddingEventRetriever:
    """Dense episodic retrieval with lexical and temporal hybrid fusion."""

    def __init__(
        self,
        model_name: str,
        device: str = "cuda",
        encoder: object | None = None,
    ):
        if encoder is None:
            from sentence_transformers import SentenceTransformer

            encoder = SentenceTransformer(model_name, device=device)
        self.encoder = encoder
        self.model_name = model_name
        self.device = device
        self._cache: dict[str, Any] = {}

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    def _event_embeddings(self, events: list[dict[str, str]]):
        fingerprint = hashlib.sha256(
            json.dumps(events, sort_keys=True).encode("utf-8")
        ).hexdigest()
        if fingerprint not in self._cache:
            self._cache[fingerprint] = self.encoder.encode(
                [event["text"] for event in events],
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        return self._cache[fingerprint]

    def retrieve(
        self,
        events: list[dict[str, str]],
        question: str,
        system: str,
        window_size: int,
        top_k: int,
    ) -> list[dict[str, str]]:
        if system == "window":
            return events[-window_size:]
        embeddings = self._event_embeddings(events)
        query = self.encoder.encode(
            [question],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        dense_scores = embeddings @ query
        query_terms = self._tokens(question)
        scored = []
        for position, (event, dense) in enumerate(zip(events, dense_scores)):
            terms = self._tokens(event["text"])
            lexical = len(query_terms & terms) / (len(query_terms | terms) or 1)
            recency = position / max(1, len(events) - 1)
            score = float(dense)
            if system == "hybrid":
                score = 0.70 * float(dense) + 0.25 * lexical + 0.05 * recency
            scored.append((score, position, event))
        return [
            event
            for _, _, event in sorted(scored, key=lambda item: (item[0], item[1]), reverse=True)[:top_k]
        ]

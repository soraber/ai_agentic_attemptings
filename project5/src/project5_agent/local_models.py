from __future__ import annotations

import json
from typing import Any


def extract_json_object(text: str) -> dict[str, Any]:
    """Decode the first complete JSON object without relying on fence formatting."""
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
    raise ValueError("Local model returned no valid JSON object")


class TransformersJSONGenerator:
    """Lazy BF16 causal-LM backend intended for a Colab A100 runtime."""

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

    def generate(self, system: str, payload: dict[str, Any], max_new_tokens: int) -> str:
        import torch

        messages = [
            {"role": "system", "content": system},
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


class EmbeddingSchemaRetriever:
    """Dense cosine retrieval over the small, fixed schema catalog."""

    def __init__(self, catalog: dict[str, str], model_name: str, device: str = "cuda"):
        from sentence_transformers import SentenceTransformer

        self.tables = sorted(catalog)
        self.model_name = model_name
        self.device = device
        self.encoder = SentenceTransformer(model_name, device=device)
        documents = [f"table {name}: {catalog[name]}" for name in self.tables]
        self.embeddings = self.encoder.encode(
            documents,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def retrieve(self, question: str, top_k: int = 5) -> list[str]:
        query = self.encoder.encode(
            [question],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        scores = self.embeddings @ query
        order = scores.argsort()[::-1][:top_k]
        return [self.tables[int(index)] for index in order]

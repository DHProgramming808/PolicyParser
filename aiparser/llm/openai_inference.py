from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .base import CodeInferenceModel
from ..models import RetrievedConcept, InferredCode


_SYSTEM = (
    "You are a medical coding assistant.\n"
    "You will be given policy text and a list of candidate code+concept pairs.\n"
    "Your job is to select the best matching codes.\n"
    "Return ONLY valid JSON. No markdown. No extra text.\n"
)

# We keep the output schema exactly aligned with InferredCode.
_SCHEMA_EXAMPLE = {
    "inferred": [
        {
            "code": "12345",
            "confidence": 0.12,
            "score": 0.12,
            "matched_concepts": ["..."],
            "justification": "..."
        }
    ]
}


def _candidates_for_prompt(retrieved: List[RetrievedConcept], max_codes: int = 30, max_per_code: int = 2):
    """
    Convert RetrievedConcept list into compact candidates to keep prompt size bounded.
    Group by code, keep top concepts per code by retrieval score.
    """
    by_code: Dict[str, List[RetrievedConcept]] = {}
    for rc in retrieved:
        code = rc.concept.code
        by_code.setdefault(code, []).append(rc)

    # sort each code bucket by score desc, keep top per code
    items = []
    for code, concepts in by_code.items():
        concepts_sorted = sorted(concepts, key=lambda x: x.score, reverse=True)[:max_per_code]
        # Use the underlying concept string; your models use rc.concept.concept
        items.append(
            {
                "code": code,
                "concepts": [c.concept.concept for c in concepts_sorted],
                "best_retrieval_score": float(concepts_sorted[0].score) if concepts_sorted else 0.0,
            }
        )

    # rank codes by best retrieval score desc
    items.sort(key=lambda x: x["best_retrieval_score"], reverse=True)
    return items[:max_codes]


class OpenAIInferenceModel(CodeInferenceModel):
    """
    Drop-in replacement for MockCodeInferenceModel using OpenAI.

    Keeps:
      - method signature: infer_codes(input_text, retrieved_concepts)
      - output: List[InferredCode]
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_s: float = 60.0,
    ) -> None:
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        self._client = OpenAI(api_key=api_key, base_url=base_url or os.getenv("OPENAI_BASE_URL"))
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self._timeout_s = timeout_s

    def infer_codes(self, input_text: str, retrieved_concepts: List[RetrievedConcept]) -> List[InferredCode]:
        candidates = _candidates_for_prompt(
            retrieved_concepts,
            max_codes=30,
            max_per_code=2,
        )

        user_prompt = (
            "POLICY TEXT:\n"
            f"{input_text}\n\n"
            "CANDIDATE CODES (ranked):\n"
            f"{json.dumps(candidates, ensure_ascii=False)}\n\n"
            "Return JSON with this exact shape:\n"
            f"{json.dumps(_SCHEMA_EXAMPLE, ensure_ascii=False)}\n\n"
            "Rules:\n"
            "- Choose up to 25 codes.\n"
            "- confidence and score must be numbers between 0 and 1.\n"
            "- matched_concepts must be drawn from the candidate concepts.\n"
            "- justification must be short and specific.\n"
            "- Return ONLY JSON.\n"
        )

        resp = self._client.chat.completions.create(
            model=self._model,
            temperature=0.0,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            timeout=self._timeout_s,
        )

        content = (resp.choices[0].message.content or "").strip()

        # Strict JSON parse (we'll add better error handling later)
        data = json.loads(content)
        inferred = data.get("inferred", []) or []

        out: List[InferredCode] = []
        for item in inferred:
            code = str(item.get("code", "")).strip()
            if not code:
                continue

            confidence = float(item.get("confidence", 0.0))
            score = float(item.get("score", confidence))
            matched_concepts = list(item.get("matched_concepts", []) or [])
            justification = str(item.get("justification", "")).strip()

            out.append(
                InferredCode(
                    code=code,
                    confidence=round(confidence, 2),
                    score=score,
                    matched_concepts=matched_concepts,
                    justification=justification,
                )
            )

        out.sort(key=lambda x: x.score, reverse=True)
        return out

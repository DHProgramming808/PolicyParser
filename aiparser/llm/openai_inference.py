from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional

from openai import OpenAI, api_key, api_key

from .base import CodeInferenceModel
from ..models import RetrievedConcept, InferredCode


DEFAULT_PROMPT = (
    "You will be given some text and a list of candidate code+concept pairs.\n"
    "Your job is to select the best matching codes.\n"
    "Return ONLY valid JSON. No markdown. No extra text.\n"
)

def build_infer_schema(name: str = "inferred_codes_response") -> Dict[str, Any]:
    return {
        "name": name,          # REQUIRED by API
        "strict": True,        # strongly recommended
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "inferred": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "code": {"type": "string"},
                            "confidence": {"type": "number"},
                            "score": {"type": "number"},
                            "matched_concepts": {"type": "array", "items": {"type": "string"}},
                            "justification": {"type": "string"},
                        },
                        "required": ["code", "confidence", "score", "matched_concepts", "justification"],
                    },
                }
            },
            "required": ["inferred"],
        },
    }


def _candidates_for_prompt(retrieved: List[RetrievedConcept], max_codes: int = 30, max_per_code: int = 3):
    """
    Convert RetrievedConcept list into compact candidates to keep prompt size bounded.
    Group by code, keep top concepts per code by retrieval score.
    """
    by_code: Dict[str, List[RetrievedConcept]] = {}
    for retrieved_concept in retrieved:
        code = retrieved_concept.concept.code
        by_code.setdefault(code, []).append(retrieved_concept)

    # sort each code bucket by score desc, keep top per code
    items = []
    for code, concepts in by_code.items():
        concepts_sorted = sorted(concepts, key = lambda x: x.score, reverse = True)[:max_per_code]
        items.append(
            {
                "code": code,
                "concepts": [c.concept.concept for c in concepts_sorted],
                "best_retrieval_score": float(concepts_sorted[0].score) if concepts_sorted else 0.0,
            }
        )

    items.sort(key = lambda x: x["best_retrieval_score"], reverse = True)
    return items[:max_codes]


def _set_prompt(custom_prompt: str) -> str:
    if (custom_prompt is None or custom_prompt.strip() == ""):
        return DEFAULT_PROMPT
    return custom_prompt.strip()

def _set_schema(custom_schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if (custom_schema is None
        or custom_schema.get("name")
        or "schema" not in custom_schema
        or not isinstance(custom_schema["schema"], dict)
        or "strict" not in custom_schema):
        sys.stderr.write("Invalid custom schema provided, falling back to default schema.\n")
        return build_infer_schema()
    
    return custom_schema

def _set_api_key(api_key: Optional[str]) -> Optional[str]:
    if api_key is not None and api_key.strip() != "":
        return api_key.strip()
    
def _set_base_url(base_url: Optional[str]) -> Optional[str]:
    if base_url is not None and base_url.strip() != "":
        return base_url.strip()
    return None

def _set_model(model: Optional[str]) -> str:
    if model is not None and model.strip() != "":
        return model.strip()
    return "gpt-4o"  # default model

def _set_client(api_key: str, base_url: str) -> OpenAI:
    try:
        return OpenAI(api_key=api_key, base_url=base_url)
    except Exception as e:
        sys.stderr.write(f"Error initializing OpenAI client: {e}\nDefaulting to environment variables.\n")
        
    # get from environment as fallback
    env_api_key = os.getenv("OPENAI_API_KEY")
    env_base_url = os.getenv("OPENAI_BASE_URL")
    if not env_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment variables.") 
    return OpenAI(api_key=env_api_key, base_url=env_base_url)

def _build_prompt(input_text: str, candidates: List[Any], schema: Dict[str, Any]) -> str:
    return (
        "POLICY TEXT:\n"
        f"{input_text}\n\n"
        "CANDIDATE CODES AND CONCEPTS:\n"
        f"{json.dumps(candidates, ensure_ascii=False)}\n\n"
        "Return JSON with this exact shape:\n"
        f"{json.dumps(schema, ensure_ascii=False)}\n\n"        
        "- code: the inferred code\n"
        "- confidence: a number between 0 and 1 indicating confidence\n"
        "- score: a numeric score (can be same as confidence or different)\n"
        "- matched_concepts: list of concept strings that supported this inference\n"
        "- justification: a string explanation of why this code was inferred based on the input and candidates\n"
    )


class OpenAIInferenceModel(CodeInferenceModel):

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_s: float = 120.0,
        custom_prompt: Optional[str] = None,
        custom_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._model = _set_model(model)
        self._client = _set_client(api_key, base_url)
        self._prompt = _set_prompt(custom_prompt)
        self._schema = _set_schema(custom_schema)
        self._api_key = api_key
        self._base_url = base_url
        self._timeout_s = timeout_s


    def infer_codes(self, input_text: str, retrieved_concepts: List[RetrievedConcept]) -> List[InferredCode]:
        candidates = _candidates_for_prompt(
            retrieved_concepts,
            max_codes=30,
            max_per_code=3,
        )

        use_case_prompt = _build_prompt(input_text, candidates, self.schema)

        response = self._client.chat.completions.create(
            model = self._model,
            temperature = 0.0,
            messages = [
                {"role": "system", "content": self._prompt},
                {"role": "user", "content": use_case_prompt},
            ],
            timeout = self._timeout_s,
        )

        content = (response.choices[0].message.content or "").strip()
        
        # Strict JSON parse TODO add better error handling and validation
        data = json.loads(content)
        inferred = data.get("inferred", []) or []

        out: List[InferredCode] = []
        for item in inferred:
            code = str(item.get("code", "")).strip()
            if not code:
                continue

            confidence = float(item.get("confidence", 0.0))
            score = float(item.get("score", retrieved_concepts["code"].score if retrieved_concepts else 0.0))
            matched_concepts = list(item.get("matched_concepts", []) or [])
            justification = str(item.get("justification", "")).strip()

            out.append(
                InferredCode(
                    code = code,
                    confidence = round(confidence, 2),
                    score = score,
                    matched_concepts = matched_concepts,
                    justification = justification
                )
            )
        
        out.sort(key = lambda x: x.score, reverse = True)
        return out
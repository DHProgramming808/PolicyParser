from __future__ import annotations

import json
import os
import sys

from typing import List, Dict, Optional, Any
from dataclasses import asdict

from openai import OpenAI

from ..models.models import ValidationAuditTrail, Concept, InferenceResult, InferenceAccuracyEvaluation, RetrievalRealCrossReference, RetrievalInferenceCrossCheck, InferenceRealCrossReference


INFERENCE_EVALUATION_PROMPT = (
    "You will be given some text, the inferred codes from a code-concept pair found in the text using AI, and the real codes extracted from the text by humans"
    "You job is to evaluate the precision/recall of these inferred codes against the real codes of concepts found in the text. You will give reasons for why a code was a false positive or why a code was a false negative"
    "Return ONLY valid JSON. No markdown. No extra text.\n"
)

def build_evaluation_schema(name: str = "text_code_evaluation_response") -> Dict[str, Any]:
    return {
        "name": name,
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "evaluation": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "code": {"type": "string"},
                            "code_inference_state": {"type": "string"},
                            "eval": {"type": "string"},
                            "notes": {"type": "string"} # TODO change to list of notes not just a single string
                        },
                        "required": ["code", "code_inference_state", "eval", "notes"],
                    },
                }
            },
            "required": ["evaluation"],
        },
    }

def _set_prompt(custom_prompt: str) -> str:
    if (custom_prompt is None or custom_prompt.strip() == ""):
        return INFERENCE_EVALUATION_PROMPT
    return custom_prompt.strip()

def _set_schema(custom_schema: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if (
        custom_schema is None
        or not isinstance(custom_schema, dict)
        or not custom_schema.get("name")
        or "schema" not in custom_schema
        or not isinstance(custom_schema["schema"], dict)
    ):
        return build_evaluation_schema()
    
    custom_schema.setdefault("strict", True)
    return custom_schema

def _set_api_key(api_key: Optional[str]) -> Optional[str]:
    if api_key is not None and api_key.strip() != "":
        return api_key.strip()
    env_key = os.getenv("OPENAI_API_KEY", "").strip()
    if env_key:
        return env_key
    return None
    
def _set_base_url(base_url: Optional[str]) -> Optional[str]:
    if base_url is not None and base_url.strip() != "":
        return base_url.strip()
    env_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if env_url: 
        return env_url.strip()
    return None  # will use OpenAI default

def _set_model(model: Optional[str]) -> str:
    if model is not None and model.strip() != "":
        return model.strip()
    return "gpt-4o"  # default model

def _set_client(api_key: Optional[str], base_url: Optional[str]) -> OpenAI:
    key = (api_key or os.getenv("OPENAI_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip()
    return OpenAI(api_key=key, base_url=url)


def _build_evaluate_inference_prompt(original_text: str, inference_cross_reference: InferenceRealCrossReference) -> str:


    correct_codes = [
        {
            "code": inferred_code.code,
            "concept": inferred_code.matched_concepts[0] if inferred_code.matched_concepts else None,
        }
        for inferred_code in inference_cross_reference.correct_codes
    ]

    wrong_codes = [
        {
            "code": inferred_code.code,
            "concept": inferred_code.matched_concepts[0] if inferred_code.matched_concepts else None,
        }
        for inferred_code in inference_cross_reference.wrong_codes
    ]

    missed_codes = [
        {
            "code": concept.code,
            "concept": concept.concept,
        }
        for concept in inference_cross_reference.missed_codes
    ]
    
    
    return (
        "ORIGINAL_TEXT:\n"
        f"{original_text}\n\n"
        "CORRECTLY INFERRED CODES AND CONCEPTS:\n"
        f"{json.dumps(correct_codes, ensure_ascii = False)}\n\n"
        "WRONGLY INFERRED CODES AND CONCEPTS (FALSE POSITIVES):\n"
        f"{json.dumps(wrong_codes, ensure_ascii = False)}\n\n"
        "MISSED CODES AND CONCEPTS (FALSE NEGATIVES):\n"
        f"{json.dumps(missed_codes, ensure_ascii = False)}\n\n"
        "Return JSON with key 'inferred' (array). Each item must have:\n"
        "code (string), code_inference_state (whether the code was correctly inferred, wrongly inferred, or missed), eval (why the code was correct, wrong, or missed), notes (if code was wrong or missed, notes on how to improve llm inference and retrieval of these codes based on the concepts and original text)"
    )

def _get_distribution_of_codes_accuracy(inference_cross_reference: InferenceRealCrossReference) -> {int, int, int}:
    num_correct_codes = len(inference_cross_reference.correct_codes)
    num_wrong_codes = len(inference_cross_reference.wrong_codes)
    num_missed_codes = len(inference_cross_reference.missed_codes)

    total_codes = sum([num_correct_codes, num_wrong_codes, num_missed_codes])

    pct_correct = (num_correct_codes * 100) // total_codes
    pct_false_pos = (num_wrong_codes * 100) // total_codes
    pct_false_neg = (num_missed_codes * 100) // total_codes

    return {pct_correct, pct_false_pos, pct_false_neg}



class OpenAIEvaluationModel():

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
        self._prompt = _set_prompt(custom_prompt)
        self._schema = _set_schema(custom_schema)
        self._api_key = _set_api_key(api_key)
        self._base_url = _set_base_url(base_url)
        self._timeout_s = timeout_s


    def evaulate_inference_accuracy(self, original_text: str, inference_cross_reference: InferenceRealCrossReference, retrieval_cross_reference: RetreivalRealCrossReference, retrieval_inference_cross_check: RetrievalInferenceCrossCheck) -> InferenceAccuracyEvaluation:
        self._client = _set_client(self._api_key, self._base_url)

        inference_evaluation_prompt = _build_evaluate_inference_prompt(original_text, inference_cross_reference)
        pct_correct, pct_false_pos, pct_false_neg = _get_distribution_of_codes_accuracy(inference_cross_reference)

        response = self._client.chat.completions.create(
            model = self._model,
            temperature = 0.0,
            response_format = {"type": "json_schema", "json_schema": self._schema},
            messages = [
                {"role": "system", "content": self._prompt},
                {"role": "user", "content": inference_evaluation_prompt}
            ],
            timeout = self._timeout_s
        )

        content = (response.choices[0].message.content or "").strip()

        data = json.loads(content)
        inference_evaluation = data.get("evaluation", []) or []

        code_evals: Dict[str, str] = {}
        for item in inference_evaluation:
            code = str(item.get("code"))
            code_inference_state = str(item.get("code_inference_state"))
            evaluation = str(item.get("eval"))
            notes = str(item.get("notes"))
            
            code_evals[code] = (code_inference_state + " | " + evaluation)

        out: InferenceAccuracyEvaluation = InferenceAccuracyEvaluation(
            pct_correct = pct_correct,
            pct_false_pos = pct_false_pos,
            pct_false_neg = pct_false_neg,
            code_evaluation = code_evals,
            notes = [notes],
        )

        return out
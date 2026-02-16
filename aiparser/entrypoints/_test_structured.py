import os
import json
import sys
import time
from typing import Any, Dict, Optional

from openai import OpenAI

# ----------------------------
# Config
# ----------------------------
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
API_KEY = os.getenv("OPENAI_API_KEY")

DEFAULT_PROMPT = (
    "Infer 2-3 likely billing codes from this short clinical note.\n"
    "Use the provided CANDIDATE CONCEPTS as your search space.\n"
    "It's okay if confidence is low.\n\n"
    "TEXT:\nPatient received an X-ray of the knee and lipid panel screening.\n\n"
    "CANDIDATE CONCEPTS:\n"
    "- Code: 73560, Concept: X-ray exam of knee 1 or 2, Score: 0.06\n"
    "- Code: 80061, Concept: Lipid panel [only when billed with ICD-10-CM code Z13.6], Score: 0.05\n"
    "- Code: 82947, Concept: Assay glucose blood quant [only when billed with ICD-10-CM code Z13.1], Score: 0.01\n"
)

# ----------------------------
# Schema builder (REAL JSON Schema)
# ----------------------------
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

# ----------------------------
# Optional overrides (prompt/schema from env)
# ----------------------------
def get_prompt() -> str:
    """
    Override with:
      $env:OPENAI_TEST_PROMPT="..."
    """
    return os.getenv("OPENAI_TEST_PROMPT", DEFAULT_PROMPT)

def get_schema() -> Dict[str, Any]:
    """
    Override schema with a file:
      $env:OPENAI_JSON_SCHEMA_PATH=".\schema.json"
    That file must contain:
      { "name": "...", "strict": true, "schema": {...} }
    """
    path = os.getenv("OPENAI_JSON_SCHEMA_PATH")
    if not path:
        return build_infer_schema()

    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    if not isinstance(loaded, dict):
        raise ValueError("Schema file must contain a JSON object.")
    if not loaded.get("name"):
        raise ValueError("Schema file missing required field: 'name'")
    if "schema" not in loaded or not isinstance(loaded["schema"], dict):
        raise ValueError("Schema file missing required field: 'schema' (must be an object)")
    if "strict" not in loaded:
        loaded["strict"] = True

    return loaded

# ----------------------------
# Core call / parse
# ----------------------------
def call_structured(client: OpenAI, prompt: str, json_schema: Dict[str, Any]) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_schema", "json_schema": json_schema},
        messages=[
            {"role": "system", "content": "Return ONLY JSON matching the schema. No markdown, no extra text."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content or ""

def parse_or_raise(s: str) -> Dict[str, Any]:
    obj = json.loads(s)
    if not isinstance(obj, dict):
        raise ValueError("Root JSON is not an object")
    inferred = obj.get("inferred")
    if not isinstance(inferred, list):
        raise ValueError("Missing or invalid 'inferred' array")
    # (Optional) light validation of item shape
    for i, item in enumerate(inferred):
        if not isinstance(item, dict):
            raise ValueError(f"inferred[{i}] is not an object")
        for key in ["code", "confidence", "score", "matched_concepts", "justification"]:
            if key not in item:
                raise ValueError(f"inferred[{i}] missing '{key}'")
    return obj

def main() -> None:
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=API_KEY)

    prompt = get_prompt()
    schema = get_schema()

    max_retries = int(os.getenv("OPENAI_STRUCTURED_RETRIES", "3"))
    base_sleep = float(os.getenv("OPENAI_STRUCTURED_BACKOFF", "0.5"))

    sys.stderr.write("Testing structured output from OpenAI API...\n")

    last_err: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            raw = call_structured(client, prompt, schema)
            data = parse_or_raise(raw)

            # IMPORTANT:
            # stdout should be JSON only (so your C# runner can safely parse it)
            sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
            return

        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(base_sleep * attempt)

    raise RuntimeError(f"Structured output test failed after {max_retries} attempts: {last_err}")

if __name__ == "__main__":
    main()

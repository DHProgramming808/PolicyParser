import json
import sys
from pathlib import Path
from typing import Any, Dict
from dataclasses import asdict


from aiparser.csv_loader import load_concepts_from_csv, CsvSchema
from aiparser.pipeline import CodeInferencePipeline, PipelineConfig
from aiparser.retriever.token_retriever import TokenRetriever
from aiparser.llm.mock_inference import MockCodeInferenceModel
from aiparser.models import AuditTrail, DictionaryAudit
from aiparser.audit_utils import sha256_text, env_fingerprint, new_run_id, utc_now_iso


# (Optional) If you want audit for single-text calls later, you can re-add it.
# For now, keep it minimal.

def build_pipeline(options: Dict[str, Any] | None = None) -> CodeInferencePipeline:
    options = options or {}

    concepts_csv = options.get("concepts_csv_path") or "aiparser/data/hcpcs.csv"
    concepts_csv_path = Path(concepts_csv)

    concepts = load_concepts_from_csv(concepts_csv_path, CsvSchema())

    retriever = TokenRetriever()
    retriever.index(concepts)

    model = MockCodeInferenceModel()

    top_k = int(options.get("top_k", 50))
    min_score = float(options.get("min_retrieval_score", 0.005))

    pipeline = CodeInferencePipeline(
        retriever = retriever,
        model = model,
        config = PipelineConfig(top_k = top_k, min_retrieval_score = min_score),
        model_info = {"name": type(model).__name__, "version": "0.2"}
    )
    return pipeline, len(concepts)


def drop_key_recursive(obj, key_to_drop: str):
    if isinstance(obj, dict):
        return {
            k: drop_key_recursive(v, key_to_drop)
            for k, v in obj.items()
            if k != key_to_drop
        }
    if isinstance(obj, list):
        return [drop_key_recursive(x, key_to_drop) for x in obj]
    return obj


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"Invalid JSON on stdin: {e}\n")
        return 2
    
    text = payload.get("text", "")
    options = payload.get("options") or {}

    if not isinstance(text, str):
        text = str(text)

    try:
        pipeline, len_concepts = build_pipeline(options)

        dictionary_audit = DictionaryAudit(
            row_count = len_concepts,
            schema={"code_col": CsvSchema().code_column, "concept_col": CsvSchema().concept_column},
        )
        audit = AuditTrail(
            run_id=new_run_id(),
            timestamp_utc=utc_now_iso(),
            input_hash=sha256_text(json.dumps(options, sort_keys = True)),
            environment=env_fingerprint(),
            dictionary=dictionary_audit,
            retrieval=None,
            model=None
        )

        raw_out = pipeline.run(text, audit_trail = audit)
        dict_out = asdict(raw_out)

        filtered = drop_key_recursive(dict_out, "input_text")
        sys.stdout.write(json.dumps(filtered))
        return 0
    except Exception as e:
        sys.stderr.write(f"Pipeline error: {e}\n")
        return 1



if __name__ == "__main__":
    raise SystemExit(main())

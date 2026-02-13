import json
import sys

from pathlib import Path
from dataclasses import asdict
from typing import List, Dict, Any

from aiparser.audit_utils import sha256_file
from aiparser.csv_loader import load_concepts_from_csv, CsvSchema
from aiparser.input_csv_loader import InputCsvSchema, load_input_data_from_csv
from aiparser.pipeline import CodeInferencePipeline, PipelineConfig
from aiparser.models import AuditTrail, DictionaryAudit, InferenceResult, InferredCode, Concept, Input, Output

from aiparser.retriever.token_retriever import TokenRetriever
from aiparser.llm.mock_inference import MockCodeInferenceModel

from aiparser.audit_utils import env_fingerprint, new_run_id, utc_now_iso

def main(input: str, output: str):
    # load concepts and input data initialize
    concepts_csv_path = Path("aiparser/data/hcpcs.csv")
    input_path = Path("aiparser/" + input)

    outputs_path = Path("aiparser/")
    outputs_file_name = output

    concepts = load_concepts_from_csv(concepts_csv_path, CsvSchema())
    sys.stderr.write(f"Loaded {len(concepts)} concepts from data directory.")
    inputs = load_input_data_from_csv(input_path, InputCsvSchema()) 
    sys.stderr.write(f"Loaded {len(inputs)} input items from {input_path}.")

    #initialize pipeline components
    retriever = TokenRetriever() # modular retriever that can later be swapped out for an embedding RAG retriever
    retriever.index(concepts)
    sys.stderr.write("[test] Retriever indexed concepts.")

    model = MockCodeInferenceModel() # modular inference model that can later be swapped out for an actual LLM-based inference model
    pipeline = CodeInferencePipeline(
        retriever = retriever,
        model = model,
        config = PipelineConfig(top_k=50, min_retrieval_score=0.005),
        model_info = {"name": "MockCodeInferenceModel", "version": "1.0"}
    )

    #setup Audit Trail
    dictionary_audit = DictionaryAudit(
        row_count=len(concepts),
        schema={"code_col": CsvSchema().code_column, "concept_col": CsvSchema().concept_column},
    )

    # run pipeline on inputs and build results single JSON output file
    results = []
    for i, input in enumerate(inputs):

        audit = AuditTrail(
            run_id=new_run_id(),
            timestamp_utc=utc_now_iso(),
            input_hash=sha256_file(input_path),
            environment=env_fingerprint(),
            dictionary=dictionary_audit,
            retrieval=None,
            model=None
        )

        raw_out = pipeline.run(input.text, audit_trail=audit)
        out = raw_out.to_json_dict()

        inferred_codes = out.get("inferred_codes", [])
        audit_trail = out.get("audit", None)
        assert isinstance(inferred_codes, list), f"Expected 'inferred_codes' to be a list, got {type(inferred_codes)}"
        
        inferrence_output = Output(
            id = input.id,
            name = input.name,
            inferred_codes = inferred_codes,
            audit = audit_trail
        )
        results.append(inferrence_output)

    # write results to output file
    outputs_path.mkdir(parents=True, exist_ok=True)
    payload = [asdict(r) for r in results]
    with open(outputs_path / outputs_file_name, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


if __name__ == "__main__":
    main(input="data/policies_cleaned.csv", output="outputs.json")
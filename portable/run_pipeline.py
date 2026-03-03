from __future__ import annotations

import json
import sys
import os

from pathlib import Path
from dataclasses import asdict
from typing import List, Dict, Any

from src.models.models import Input, Output, Concept, CorrectPolicyCodes, RetrievedConcept, DictionaryAudit, AuditTrail
from src.utils.csv_utils import load_input_data_from_csv, load_concepts_from_csv, load_correct_policy_concepts, InputCsvSchema, ConceptCodeCsvSchema, PolicyCodeCsvSchema
from src.utils.audit_utils import sha256_file, sha256_text, utc_now_iso, new_run_id, env_fingerprint

from src.retrieval.openai_embedding_retriever import OpenAIEmbeddingRetriever
from src.inference.openai_inference import OpenAIInferenceModel
from src.pipelines.simple_text_inference_pipeline import SimpleTextCodeInferencePipeline




def main(input: str = "", validation: str = "", out: str = "", api_key: str = ""):
    #load concepts and input data initialize
    input = "policies_cleaned_mini.csv"
    validation = "policies_cleaned_labels_mini.csv"
    out = "output.json"

    concepts_csv_path = Path("data/hcpcs.csv")
    input_path = Path("data/" + input)
    validation_csv_path = Path("data/" + validation)
    out_path = Path("data/")

    concepts: List[Concept] = load_concepts_from_csv(concepts_csv_path, ConceptCodeCsvSchema())
    sys.stdout.write(f"Loaded {len(concepts)} concepts from data dictionary\n\n")

    inputs: List[Input] = load_input_data_from_csv(input_path, InputCsvSchema())
    sys.stdout.write(f"Loaded {len(inputs)} inputs from data dictionary\n\n")

    real_codes: List[CorrectPolicyCodes] = load_correct_policy_concepts(validation_csv_path, PolicyCodeCsvSchema())
    sys.stdout.write(f"Loaded {len(real_codes)} from data dictionary\n\n")


    #OpenAI key
    oai_key = ""
    if api_key is not None and api_key.strip() != "":
        oai_key = api_key.strip()
    env_key = os.getenv("OPENAI_API_KEY", "").strip()
    if env_key:
        oai_key = env_key

    oai_key = ""

    sys.stdout.write(f"Using api key: {oai_key} || {env_key}\n\n")
    
    #set up RAG Model
    retriever: OpenAIEmbeddingRetriever = OpenAIEmbeddingRetriever(
        api_key = oai_key,
        base_url = "https://api.openai.com/v1",
        embedding_model = "text-embedding-3-small",
        batch_size = 32,
    )

    #set up Inference Model
    inference_model: OpenAIInferenceModel = OpenAIInferenceModel(
        api_key = oai_key,
        model = "gpt-4o-mini",
        base_url = "https://api.openai.com/v1",
    )

    #set up Inference Pipeline
    pipeline: SimpleTextCodeInferencePipeline = SimpleTextCodeInferencePipeline(
        retriever = retriever,
        inference_model = inference_model,
        model_info = {"name": "OpenAIInferenceModel", "version": "1.0"}
    )

    dictionary_audit = DictionaryAudit(
        row_count=len(concepts),
        schema={"code_col": ConceptCodeCsvSchema().code_column, "concept_col": ConceptCodeCsvSchema().concept_column},
    )

    #Run inference pipeline
    results: List[Output] = []
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

        raw_out = pipeline.run(input.text, audit_trail = audit)
        out = asdict(raw_out)

        inferred_codes = out.get("inferred_codes", [])
        audit_trail = out.get("audit", None)
        assert isinstance(inferred_codes, list), f"Expected 'inferred_codes' to be a list, got {type(inferred_codes)}"
    
        inference_output = Output(
            id = input.id,
            name = input.name,
            inferred_codes = inferred_codes,
            audit = audit_trail
        )
        results.append(inference_output)

    #create output
    out_path.mkdir(parents = True, exist_ok = True)
    mock_payload = [asdict(r) for r in results]
    with open(out_path / out, "w", encoding = "utf-8") as f:
        json.dump(mock_payload, f, indent = 2)


if __name__ == "__main__":
    main(input = "policies_cleaned_mini.csv", validation = "policies_cleaned_lables_mini.csv", out = "output.json", api_key = "")
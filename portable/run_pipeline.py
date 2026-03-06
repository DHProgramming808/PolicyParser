from __future__ import annotations

import json
import sys
import os

from pathlib import Path
from dataclasses import asdict
from typing import List, Dict, Any

from src.models.models import Input, Output, Concept, CorrectPolicyCodes, RetrievedConcept, DictionaryAudit, AuditTrail, InferenceResult, InferenceAccuracyEvaluation, RetrievalCandidateAudit, InferredCode
from src.utils.csv_utils import load_input_data_from_csv, load_concepts_from_csv, load_correct_policy_concepts, InputCsvSchema, ConceptCodeCsvSchema, PolicyCodeCsvSchema
from src.utils.audit_utils import sha256_file, sha256_text, utc_now_iso, new_run_id, env_fingerprint

from src.retrieval.openai_embedding_retriever import OpenAIEmbeddingRetriever
from src.inference.openai_inference import OpenAIInferenceModel
from src.validation.openai_inference_evaluation import OpenAIEvaluationModel


from src.pipelines.simple_text_inference_pipeline import SimpleTextCodeInferencePipeline
from src.pipelines.code_precision_recall_evaluation_pipeline import SimpleInferenceEvaluationPipeline


def find_correct_codes(text_id: str, correct_codes: List[CorrectPolicyCodes]) -> List[Concept]:
    for i, cpc in enumerate(correct_codes):
        if text_id == cpc.policy_id:
            return cpc.codes
        
    return []


def main(input: str = "", validation: str = "", out: str = "", api_key: str = ""):
    #load concepts and input data initialize
    input = "policies_cleaned_mini.csv"
    validation = "policies_cleaned_labels_mini.csv"
    out_file = "output.json"

    #test stub for evaluation
    evaluation_file = "evaluation.json"

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


    sys.stdout.write(f"Using api key: {oai_key}\n\n")
    
    #set up RAG Model
    retriever: OpenAIEmbeddingRetriever = OpenAIEmbeddingRetriever(
        api_key = oai_key,
        base_url = "https://api.openai.com/v1",
        embedding_model = "text-embedding-3-small",
        batch_size = 32,
    )
    retriever.index(concepts)

    #set up Inference Model
    inference_model: OpenAIInferenceModel = OpenAIInferenceModel(
        api_key = oai_key,
        model = "gpt-4o-mini",
        base_url = "https://api.openai.com/v1",
    )

    #setup Evaluation Model
    evaluation_model: OpenAIEvaluationModel = OpenAIEvaluationModel(
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

    #set up Inference Evaluation Pipeline
    evaluation_pipeline: SimpleInferenceEvaluationPipeline = SimpleInferenceEvaluationPipeline(
        evaluation_model = evaluation_model
    )

    #Run inference pipeline
    results: List[Output] = []
    raw_results: List[InferenceResult] = []
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

        raw_out: InferenceResult = pipeline.run(input.text, audit_trail = audit)
        out = asdict(raw_out)

        inferred_codes = out.get("inferred", [])
        audit_trail = out.get("audit", None)
        assert isinstance(inferred_codes, list), f"Expected 'inferred_codes' to be a list, got {type(inferred_codes)}"
    
        #format output
        inference_output = Output(
            id = input.id,
            name = input.name,
            inferred_codes = inferred_codes,
            audit = audit_trail
        )
        results.append(inference_output)
        raw_results.append(raw_out)


    #Run Evluation pipeline
    evaluation_results: List[InferenceAccuracyEvaluation] = []
    for i, raw_out in enumerate(raw_results):
        audit = AuditTrail(
            run_id=new_run_id(),
            timestamp_utc=utc_now_iso(),
            input_hash=sha256_file(input_path),
            environment=env_fingerprint(),
            dictionary=dictionary_audit,
            retrieval=None,
            model=None
        )

        original_text: str = raw_out.input_text
        inferred_codes: List[InferredCode] = raw_out.inferred
        retrieval_codes: List[RetrievalCandidateAudit] = raw_out.audit.retrieval.candidates

        #find correct codes for evaluation pipeline
        correct_code_concepts = find_correct_codes(input.id, real_codes)
        correct_codes: Dict[str, str] = {}
        for cc in correct_code_concepts:
            correct_codes[cc.code] = cc.concept

        evaluation_raw_out: InferenceAccuracyEvaluation = evaluation_pipeline.run(original_text, inferred_codes, retrieval_codes, correct_codes, audit)
        
        #test stub
        evaluation_out = asdict(evaluation_raw_out)
        evaluation = InferenceAccuracyEvaluation(
            pct_correct = 100,
            pct_false_pos = 50,
            pct_false_neg = 0,
            code_evaluation = {"test": "test"},
            notes = ["testest"]
        )
        evaluation_results.append(evaluation_raw_out)


    #create output
    out_path.mkdir(parents = True, exist_ok = True)
    payload = [asdict(r) for r in results]
    with open(out_path / out_file, "w", encoding = "utf-8") as f:
        json.dump(payload, f, indent = 2)

    #create evaluation output # just add to regular output
    out_path.mkdir(parents = True, exist_ok = True)
    evaluation_payload = [asdict(r) for r in evaluation_results]
    with open(out_path / evaluation_file, "w", encoding = "utf-8") as f:
        json.dump(evaluation_payload, f, indent = 2)


if __name__ == "__main__":
    main(input = "policies_cleaned_mini.csv", validation = "policies_cleaned_lables_mini.csv", out = "output.json", api_key = "")
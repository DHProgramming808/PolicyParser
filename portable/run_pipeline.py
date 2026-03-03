from __future__ import annotations

import json
import sys

from pathlib import Path
from dataclasses import asdict
from typing import List, Dict, Any

from src.models.models import Input, Output, Concept, CorrectPolicyCodes, RetrievedConcept
from src.utils.csv_utils import load_input_data_from_csv, load_concepts_from_csv, load_correct_policy_concepts, InputCsvSchema, ConceptCodeCsvSchema, PolicyCodeCsvSchema

from src.retrieval.openai_embedding_retriever import OpenAIEmbeddingRetriever




def main(input: str = "", validation: str = "", out: str = ""):
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

    
    #RAG
    retriever: OpenAIEmbeddingRetriever = OpenAIEmbeddingRetriever(
        api_key = ,
        base_url = "https://api.openai.com/v1",
        embedding_model = "text-embedding-3-small",
        batch_size = int(options.get("embedding_batch_size", 32)),
    )

    retriever.index(concepts)
    embdedded_concepts: List[RetrievedConcept]









    out_path.mkdir(parents = True, exist_ok = True)
    mock_payload = [asdict(r) for r in real_codes]
    with open(out_path / out, "w", encoding = "utf-8") as f:
        json.dump(mock_payload, f, indent = 2)


if __name__ == "__main__":
    main(input = "policies_cleaned_mini.csv", validation = "policies_cleaned_lables_mini.csv", out = "output.json")
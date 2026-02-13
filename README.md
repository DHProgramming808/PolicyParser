# PolicyParser

A lightweight RAG-based inference engine that maps input policy text to code-concept pairs using:

- Token-based retrieval (local RAG)
- Pluggable inference model (mock v1, LLM-ready)
- Full audit/provenance trail per input document
- Deterministic JSON output

---

## Project Structure

PolicyParser/
│
├── aiparser/
│ ├── run_pipeline.py # CLI entrypoint
│ ├── pipeline.py # Core orchestration
│ ├── csv_loader.py # Concept dictionary loader
│ ├── input_csv_loader.py # Input document loader
│ ├── retriever/
│ │ └── token_retriever.py
│ ├── llm/
│ │ └── mock_inference.py
│ ├── models.py
│ └── audit_utils.py
│
├── data/
│ ├── hcpcs.csv # Code-concept dictionary
│ └── policies_cleaned.csv # Input documents
│
└── outputs.json # Generated output (example)

---

## How to Run

### Clone the repository

```bash
git clone 
cd PolicyParser

python -m venv policyparser

policyparser\Scripts\activate

# v1 only uses standard Python library
# pip install -r requirements.txt

python -m aiparser.run_pipeline --input [input.csv] --output [output.json]
# default will pull policies_cleaned.csv
# other files should be placed in PolicyParser/ (root)

---

## Input

input schema is:

id,name,text
1,Policy A,"Long policy document text..."
2,Policy B,"Another document..."

## Output

output json schema is:

[
  {
    "id": "1",
    "name": "Policy A",
    "inferred_codes": [
      {
        "code": "J1234",
        "confidence": 0.82,
        "justification": "Matched concept ..."
      }
    ],
    "audit": {
      "run_id": "...",
      "timestamp_utc": "...",
      "input_sha256": "...",
      "dictionary": {...},
      "retrieval": {...},
      "model": {...},
      "environment": {...}
    }
  }
]


## Architecture Overview

1. Retrieval Layer

Token-based overlap scoring (Jaccard-style similarity)
Configurable top_k and min_retrieval_score
Returns candidate concepts for inference
Designed for swap to RAG/vector db/embedded tokens

2. Inference Layer

Mock inference model (v1)
Structured output format
Designed for seamless swap to LLM implementation

3. Audit Trail

Each run captures:
Input SHA256 hash
Dictionary file hash
Retrieval candidates and scores
Model metadata
Environment fingerprint
This enables reproducibility and controlled reruns.

4. Considerations

Modular architecture
Clear separation of retrieval and inference
Deterministic audit trail
Reproducibility as a first-class feature
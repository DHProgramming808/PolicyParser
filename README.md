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

###


## Design Considerations

Design Key Points:
-Clarity of data schemes:
	Use of models.py to explicitly set input/output contracts, as well as to standardize internal data models for modularity
	Use of base classes to explicitly set method signatures for modularity
	When hitting openai api, use of infer schema for robust responses from LLMs


-Handling uncertainty:
	Use of confidence and scores as a metric of uncertain codes.
	Currently uncertainty is recorded but not handled, but with the way data is structured, it would be simple to implement
	Future plans to chunk input text instead of a single ingestion event would help narrow down uncertainty and keep context windows small for better clarity


-System designs and tradeoffs:
	Modular structure slows down MVP development
	Redundant inference schema checks introduce latency and development costs
	Non-agentic system allows for faster inference and development, but introduces potential misses in parsing.
	C# API wrapper allows for use-case factory pattern for expandability, but introduces a weaklink between python code and api + lack of persistence of data memory for faster inference
	Current batch-inference re-runs through whole pipeline and does not use memory persistence.


-Code Organization and readability:
	Modular structure allows for readability. 
	Orechestration module - pipeline.py - sets up configs, inits relevant modules, sets up audit trail
	API MVC layer cleanly separates backend API layer from inference layer


-Maintainability and data quality:
	Modular structure allows for natural growth and maintainability. 
	Base class does introduce OOP-like parent-child maintenance overhead, but for vertical modularity, the tradeoff is acceptable.
	Audit trail records specific inference settings, for reproducibility and diagnose issues with specific modules.
	API factory pattern allows for a single controller to be able to handle different use-cases


Future improvements:

-Chunking input strings
-Add reference csv input
-Add batch input UX
-Format output
-Add more usecases
-Add explicit code parsing (regex)
-Cleanup audit objects (add temperature and seed)
-Enable data caching and memory persistence in the python layer



## Inference Module Architecture Overview

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

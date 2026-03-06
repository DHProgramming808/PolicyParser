# PolicyParser Portable Pipeline

This project runs an **AI-assisted policy code extraction pipeline**.  
It loads healthcare policy text, retrieves relevant HCPCS concepts using embeddings, performs LLM-based inference to predict policy codes, and then evaluates the predictions against labeled ground truth.

The pipeline produces two outputs:

- **output.json** → inferred codes for each policy
- **evaluation.json** → evaluation metrics for inference accuracy


---

# Overview of the Pipeline

The script performs the following steps:

1. Load **HCPCS concept dictionary**
2. Load **policy text inputs**
3. Load **ground truth policy codes** for evaluation
4. Build an **embedding index** of HCPCS concepts
5. Run **LLM inference** to predict policy codes from policy text
6. Evaluate predictions using an **LLM-based evaluation model**
7. Save results to JSON files

Architecture:

```
CSV Inputs
   │
   ▼
Concept Dictionary (HCPCS)
   │
   ▼
Embedding Retriever (OpenAI)
   │
   ▼
Inference Model (OpenAI GPT)
   │
   ▼
Evaluation Model (OpenAI GPT)
   │
   ▼
JSON Outputs
```


---

# Requirements

## Python

Python **3.10+** is recommended.

Check your version:

```
python --version
```


---

# Install Dependencies

Install required packages:

```
pip install openai
```

If your repo includes a `requirements.txt`, use:

```
pip install -r requirements.txt
```


---

# Project Structure

Expected folder layout:

```
project-root/
│
├── run_pipeline.py
│
├── data/
│   ├── hcpcs.csv
│   ├── policies_cleaned_mini.csv
│   ├── policies_cleaned_labels_mini.csv
│
├── src/
│   ├── models/
│   ├── pipelines/
│   ├── retrieval/
│   ├── inference/
│   ├── validation/
│   └── utils/
│
└── output/
```

Input files are read from the **data/** directory.


---

# Required Input Files

## HCPCS Concept Dictionary

```
data/hcpcs.csv
```

Contains the mapping between **medical codes** and **concept descriptions**.

Example:

```
code,concept
G0008,Administration of influenza virus vaccine
99213,Office visit established patient
```


---

## Policy Text Dataset

```
data/policies_cleaned_mini.csv
```

Contains policy text used for inference.

Example:

```
id,name,text
policy_001,Influenza Vaccine Policy,"Administration of influenza vaccine is covered..."
```


---

## Ground Truth Labels

```
data/policies_cleaned_labels_mini.csv
```

Contains the correct policy codes used for evaluation.

Example:

```
policy_id,code
policy_001,G0008
```


---

# OpenAI API Key Setup

You must provide an **OpenAI API key**.

## Option 1 — Environment Variable (Recommended)

Linux / Mac:

```
export OPENAI_API_KEY=your_api_key_here
```

Windows PowerShell:

```
$env:OPENAI_API_KEY="your_api_key_here"
```

The script will automatically detect the environment variable.


---

## Option 2 — Pass Directly in the Script

Edit the bottom of `run_pipeline.py`:

```python
main(
    input_file="policies_cleaned_mini.csv",
    validation="policies_cleaned_labels_mini.csv",
    out_file="output.json",
    api_key="your_api_key_here"
)
```


---

# Running the Pipeline

From the project root directory:

```
python run_pipeline.py
```

The script will:

1. Load the concept dictionary
2. Load policy inputs
3. Build the embedding index
4. Run inference
5. Run evaluation
6. Write output files

Example console output:

```
Loaded 12000 concepts from data dictionary

Loaded 100 inputs from data dictionary

Loaded 100 labels from data dictionary

Using api key: sk-***********
```


---

# Output Files

Results are written to the **data/** directory.

## Inference Output

```
data/output.json
```

Example:

```json
[
  {
    "id": "policy_001",
    "name": "Influenza Vaccine Policy",
    "inferred_codes": [
      {
        "code": "G0008",
        "confidence": 0.94
      }
    ],
    "audit": {}
  }
]
```


---

## Evaluation Output

```
data/evaluation.json
```

Example:

```json
[
  {
    "pct_correct": 80,
    "pct_false_pos": 10,
    "pct_false_neg": 10,
    "code_evaluation": {
      "G0008": "correct | policy clearly references influenza vaccination"
    },
    "notes": []
  }
]
```


---

# Models Used

## Embedding Retriever

```
text-embedding-3-small
```

Used to retrieve relevant HCPCS concepts for each policy.


---

## Inference Model

```
gpt-4o-mini
```

Used to infer policy codes from text.


---

## Evaluation Model

```
gpt-4o-mini
```

Used to analyze correctness of inferred codes.


---

# Troubleshooting

## API Key Not Found

Error:

```
AuthenticationError: No API key provided
```

Fix by setting:

```
export OPENAI_API_KEY=your_key
```

or passing `api_key` in the script.


---

## CSV File Not Found

Error:

```
FileNotFoundError: data/hcpcs.csv
```

Ensure your folder structure matches:

```
data/
  hcpcs.csv
  policies_cleaned_mini.csv
  policies_cleaned_labels_mini.csv
```


---

## Rate Limits

If you run large datasets you may see:

```
RateLimitError
```

Solutions:

- reduce batch size
- add delays
- upgrade API quota


---

# Notes

- The script uses **LLM-based evaluation**, which means evaluation results may vary slightly between runs.
- For reproducible experiments, keep the dataset and prompt versions fixed.


---

# Example Run

```
(using preloaded demo files)
python run_pipeline.py

OR 

(custom files)
python run_pipeline.py \
  --concepts hcpcs.csv \
  --input policies.csv \
  --validation labels.csv \
  --output results.json

```

Output:

```
Loaded 5000 concepts from data dictionary
Loaded 100 policies
Loaded 100 labels

Running inference pipeline...
Running evaluation pipeline...

Saved:
data/output.json
data/evaluation.json
```


---

# License

Internal / experimental research pipeline.
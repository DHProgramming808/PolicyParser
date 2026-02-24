from __future__ import annotations

import sys
import csv
from dataclasses import dataclass
from typing import List, Dict, Optional

from .models import Concept


@dataclass
class CsvSchema:
    code_column: str = "code"
    concept_column: str = "description"


def load_concepts_from_csv(conceptpair_csv_path: str, schema: CsvSchema, *, encoding: str = "utf-8") -> List[Concept]:
    concepts: List[Concept] = []

    with open(conceptpair_csv_path, "r", encoding = encoding, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            raise ValueError("CSV file must have a header row with column names.")
        missing_columns = [col for col in [schema.code_column, schema.concept_column] if col not in reader.fieldnames]
        if missing_columns:
            raise ValueError(f"CSV file is missing required columns: {', '.join(missing_columns)}")

        for row_index, row in enumerate(reader, start=2):  # Start at 2 to account for header row
            code = row.get(schema.code_column or "").strip()
            concept = row.get(schema.concept_column or "").strip()

            if not code:
                sys.stderr.write(f"Warning: Missing code in row {row_index}. Skipping this row.")
                continue

            metadata = {k: v for k, v in row.items() if k not in [schema.code_column, schema.concept_column]}
            if code and concept:
                concepts.append(Concept(code=code, concept=concept, metadata=metadata))

    if not concepts:
        raise ValueError("No valid concepts were loaded from the CSV file. Please check the file content and schema.")
    
    return concepts


def concepts_by_code(concepts: List[Concept]) -> Dict[str, List[Concept]]:
    out: Dict[str, List[Concept]] = {}
    for concept in concepts:
        out.setdefault(concept.code, []).append(concept)
    return out
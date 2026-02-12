from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from typing import List, Dict, Optional

from .models import Input


@dataclass
class InputCsvSchema:
    id_column: str = "policy_id"
    name_column: str = "policy_name"
    text_column: str = "cleaned_policy_text"


def load_input_data_from_csv(input_csv_path: str, schema: InputCsvSchema, *, encoding: str = "utf-8") -> List[Dict[str, str]]:
    inputs: List[Input] = []
    csv.field_size_limit(100 * 1024 * 1024)  # Increase field size limit to handle large text fields

    with open(input_csv_path, "r", encoding = encoding, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            raise ValueError("CSV file must have a header row with column names.")
        missing_columns = [col for col in [schema.id_column, schema.name_column, schema.text_column] if col not in reader.fieldnames]
        if missing_columns:
            raise ValueError(f"CSV file is missing required columns: {', '.join(missing_columns)}")

        for row_index, row in enumerate(reader, start=2):  # Start at 2 to account for header row
            input_id = row.get(schema.id_column or "").strip()
            name = row.get(schema.name_column or "").strip()
            text = row.get(schema.text_column or "").strip()

            if not id:
                print(f"Warning: Missing id in row {row_index}. Skipping this row.")
                continue
            if not text:
                print(f"Warning: Missing text in row {row_index}. Skipping this row.")
                continue

            inputs.append(Input(id=input_id, name=name, text=text))


    if not inputs:
        raise ValueError("No valid inputs were loaded from the CSV file. Please check the file content and schema.")
    
    return inputs
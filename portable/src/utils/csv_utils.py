from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from typing import List, Dict, Optional

from ..models.models import Input, Concept, CorrectPolicyCodes


@dataclass
class InputCsvSchema:
    id_column: str = "id"
    name_column: str = "name"
    text_column: str = "text"

@dataclass
class ConceptCodeCsvSchema:
    code_column: str = "code"
    concept_column: str = "description"

@dataclass
class PolicyCodeCsvSchema:
    policy_id: str = "policy_id"
    policy_uuid: str = "policy_uuid"
    hcpcs_codes: str = "hcpcs_codes"
    icd_10_codes: str = "icd_10_codes"


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
                sys.stderr.write(f"Warning: Missing id in row {row_index}. Skipping this row.")
                continue
            if not text:
                sys.stderr.write(f"Warning: Missing text in row {row_index}. Skipping this row.")
                continue

            inputs.append(Input(id=input_id, name=name, text=text))


    if not inputs:
        raise ValueError("No valid inputs were loaded from the CSV file. Please check the file content and schema.")
    
    return inputs


def load_concepts_from_csv(conceptpair_csv_path: str, schema: ConceptCodeCsvSchema, *, encoding: str = "utf-8") -> List[Concept]:
    concepts: List[Concept] = []

    with open(conceptpair_csv_path, "r", encoding = encoding, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            raise ValueError("Code-Concept CSV file must have a header row with column names.")
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


def load_correct_policy_concepts(policy_concept_csv_path: str, schema: PolicyCodeCsvSchema, *, encoding: str = "utf-8") -> List[CorrectPolicyCodes]:
    correct_policy_codes: List[CorrectPolicyCodes] = []

    with open(policy_concept_csv_path, "r", encoding = encoding, newline = "") as csvfile:
        reader = csv.DictReader(csvfile)
        if not reader.fieldnames:
            raise ValueError("Policy Code CSV file must have a header row with column names.")
        missing_columns = [col for col in [schema.policy_id, schema.policy_uuid, schema.hcpcs_codes, schema.icd_10_codes] if col not in reader.fieldnames]
        if missing_columns:
            raise ValueError(f"CSV file is missing required columns: {', '.join(missing_columns)}")
        
        for row_index, row in enumerate(reader, start=2):  # Start at 2 to account for header row
            policy_id = row.get(schema.policy_id)
            policy_uuid = row.get(schema.policy_uuid)

            if not policy_id:
                sys.stderr.write(f"Warning: Missing policy_id in row {row_index}. Skipping this row.")
                continue

            hcpcs_codes = row.get(schema.hcpcs_codes)
            icd_10_codes = row.get(schema.icd_10_codes)

            codes: List[str] = []
            if hcpcs_codes:
                hcpcs_codes_split = hcpcs_codes.split("|")
                codes = codes + hcpcs_codes_split
            if icd_10_codes:
                icd_10_codes_split = icd_10_codes.split("|")
                codes = codes + icd_10_codes_split

            concept_codes: List[Concept] = []
            for code in codes:
                concept = Concept(
                    code = code,
                    concept = code
                )
                concept_codes.append(concept)

            correct_policy_code = CorrectPolicyCodes(
                policy_id = policy_id,
                policy_uuid = policy_uuid,
                codes = concept_codes
            )

            correct_policy_codes.append(correct_policy_code)

    if not correct_policy_codes:
        raise ValueError("No valid policy codes were loaded from the CSV file. Please check the file content and schema.")

    return correct_policy_codes


from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional



@dataclass
class Input:
    id: str
    name: str
    text: str

@dataclass
class Output:
    id: str
    name: str
    inferred_codes: List[Dict[str, Any]] = None
    audit: Optional[Dict[str, Any]] = None

@dataclass
class Concept:
    code: str
    concept: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class RetrievedConcept:
    concept: Concept
    score: float

@dataclass
class InferredCode:
    code: str
    confidence: str
    score: float
    matched_concepts: List[str]
    justification: str

@dataclass
class InferenceResult:
    input_text:str
    inferred: List[InferredCode]
    audit: AuditTrail
    model_info: Dict[str, Any] = None
    
    def to_json_dict(self) -> Dict[str, Any]:
        return {
            "input_text": self.input_text,
            "inferred_codes": [asdict(x) for x in self.inferred],
            "audit": self.audit.to_json_dict() if self.audit else None,
            "model_info": self.model_info or {}
        }
    

@dataclass
class RetrievalCandidateAudit:
    code: str
    concept: str
    retrieval_score: float


@dataclass
class RetrievalAudit:
    retriever_name: str
    retreiver_version: str
    top_k: int
    min_retrieval_score: float
    candidates: List[RetrievalCandidateAudit]


@dataclass
class ModelAudit:
    model_name: str
    model_version: str
    params: Optional[Dict[str, Any]] = None

    prompt_template: Optional[str] = None
    raw_output: Optional[str] = None
    
    model_info: Optional[Dict[str, Any]] = None


@dataclass
class DictionaryAudit:
    row_count: int
    schema: Dict[str, str]


@dataclass
class AuditTrail:
    run_id: str
    timestamp_utc: str
    input_hash: str
    dictionary: Optional[DictionaryAudit] = None
    retrieval: Optional[RetrievalAudit] = None
    model: Optional[ModelAudit] = None
    environment: Dict[str, Any] = None
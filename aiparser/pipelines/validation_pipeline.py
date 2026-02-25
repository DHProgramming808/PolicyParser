from __future__ import annotations
import sys
import json

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..data_validation.base import DataEvaluationModel
from ..models import ValidationAuditTrail

@dataclass
class ValidationPipelineConfig: # TODO configure
    temp_config: str

class ResultValidationPipeline:
    def __init__(
        self,
        dataEvaluation: DataEvaluationModel,
        config: ValidationPipelineConfig = ValidationPipelineConfig(),
        audit_trail: ValidationAuditTrail = None,
        *,
        model_info: Optional[Dict[str, Any]] = None
    ) -> None:
        self._data_evaluation_model = dataEvaluation
        self._config = config
        self._audit_trial = audit_trail
        self._model_info = model_info or {}

    def run(self, )
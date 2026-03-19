"""Tests for api/models.py — Pydantic request/response model validation."""

import pytest
from pydantic import ValidationError

from api.models import (
    PredictionRequest,
    PredictionResponse,
    ModelListResponse,
    SensorListResponse,
    SourceInfo,
    DiagnosisResponse,
    TextGenerationResponse,
    HealthResponse,
)


# ── PredictionRequest ────────────────────────────────────────────────

class TestPredictionRequest:
    def test_valid_request(self):
        req = PredictionRequest(
            independent_variables=[1.2, 3.4, 5.6],
            model_identifier="Random_Forest-valve_condition"
        )
        assert req.model_identifier == "Random_Forest-valve_condition"
        assert req.dependent_variables is None

    def test_with_dependent_variables(self):
        req = PredictionRequest(
            independent_variables=[1.0],
            dependent_variables=[0, 1],
            model_identifier="model_a"
        )
        assert req.dependent_variables == [0, 1]

    def test_missing_independent_variables_raises(self):
        with pytest.raises(ValidationError):
            PredictionRequest(model_identifier="m")

    def test_missing_model_identifier_raises(self):
        with pytest.raises(ValidationError):
            PredictionRequest(independent_variables=[1.0])


# ── PredictionResponse ───────────────────────────────────────────────

class TestPredictionResponse:
    def test_minimal_response(self):
        resp = PredictionResponse(encoded_prediction=1, model_used="RF-test")
        assert resp.encoded_prediction == 1
        assert resp.prediction is None

    def test_full_response(self):
        resp = PredictionResponse(
            encoded_prediction=2,
            model_used="LR-test",
            prediction=42,
            dependent_variables=[0, 1]
        )
        assert resp.prediction == 42
        assert resp.dependent_variables == [0, 1]


# ── ModelListResponse ────────────────────────────────────────────────

class TestModelListResponse:
    def test_valid(self):
        resp = ModelListResponse(models=["a", "b"], count=2)
        assert resp.count == 2
        assert len(resp.models) == 2

    def test_empty_list(self):
        resp = ModelListResponse(models=[], count=0)
        assert resp.models == []


# ── SensorListResponse ───────────────────────────────────────────────

class TestSensorListResponse:
    def test_valid(self):
        resp = SensorListResponse(collections=["sensor_a", "sensor_b"])
        assert "sensor_a" in resp.collections


# ── SourceInfo ───────────────────────────────────────────────────────

class TestSourceInfo:
    def test_defaults(self):
        src = SourceInfo()
        assert src.file == ""
        assert src.chunk == ""
        assert src.search_score == 0
        assert src.rerank_score is None

    def test_full(self):
        src = SourceInfo(
            file="manual.pdf",
            chunk="Replace the filter...",
            search_score=0.95,
            rerank_score=0.88
        )
        assert src.rerank_score == 0.88


# ── DiagnosisResponse ────────────────────────────────────────────────

class TestDiagnosisResponse:
    def test_minimal(self):
        resp = DiagnosisResponse(diagnosis="Check the valve")
        assert resp.sources is None
        assert resp.search_method is None

    def test_full_with_sources(self):
        resp = DiagnosisResponse(
            diagnosis="Replace bearing",
            sources=[
                SourceInfo(file="doc.pdf", chunk="bearing info", search_score=0.9)
            ],
            search_method="hybrid",
            reranker="voyage/rerank-2",
            embedding_model="voyage/voyage-3",
            completion_model="bedrock/nova-lite"
        )
        assert resp.search_method == "hybrid"
        assert len(resp.sources) == 1
        assert resp.reranker == "voyage/rerank-2"


# ── TextGenerationResponse ───────────────────────────────────────────

class TestTextGenerationResponse:
    def test_valid(self):
        resp = TextGenerationResponse(answer="The sky is blue.")
        assert resp.answer == "The sky is blue."

    def test_missing_answer_raises(self):
        with pytest.raises(ValidationError):
            TextGenerationResponse()


# ── HealthResponse ───────────────────────────────────────────────────

class TestHealthResponse:
    def test_valid(self):
        resp = HealthResponse(status="healthy", service="predictive_maintenance")
        assert resp.status == "healthy"

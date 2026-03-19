"""Tests for fastapi_mcp.py — FastAPI endpoint integration tests (httpx TestClient)."""

import sys
import pytest
from unittest.mock import patch, MagicMock

# Mock fastmcp before importing the app module (it may not be installed in test env)
sys.modules.setdefault("fastmcp", MagicMock())

from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a TestClient with mocked MongoDB and PredictionService."""
    import fastapi_mcp as app_module

    mock_service = MagicMock()
    mock_mongo = MagicMock()
    mock_mongo.admin.command.return_value = {"ok": 1}

    orig_service = app_module.prediction_service
    orig_client = app_module.client

    app_module.prediction_service = mock_service
    app_module.client = mock_mongo

    test_client = TestClient(app_module.app, raise_server_exceptions=False)

    yield test_client, mock_service

    app_module.prediction_service = orig_service
    app_module.client = orig_client


# ── Health Check ─────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        test_client, _ = client
        resp = test_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "predictive_maintenance"


# ── /api/models ──────────────────────────────────────────────────────

class TestModelsEndpoint:
    def test_list_models(self, client):
        test_client, mock_service = client
        mock_service.list_models.return_value = {
            "models": ["Random_Forest-valve_condition"],
            "count": 1
        }
        resp = test_client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert "Random_Forest-valve_condition" in data["models"]


# ── /api/sensors ─────────────────────────────────────────────────────

class TestSensorsEndpoint:
    def test_list_sensors(self, client):
        test_client, mock_service = client
        mock_service.list_sensor_collections.return_value = {
            "collections": ["sensor_a", "sensor_b"]
        }
        resp = test_client.get("/api/sensors")
        assert resp.status_code == 200
        data = resp.json()
        assert "sensor_a" in data["collections"]


# ── /api/predict ─────────────────────────────────────────────────────

class TestPredictEndpoint:
    def test_successful_prediction(self, client):
        test_client, mock_service = client
        mock_service.make_prediction.return_value = {
            "encoded_prediction": 1,
            "model_used": "RF-test",
            "prediction": 42
        }
        resp = test_client.post("/api/predict", json={
            "independent_variables": [1.0, 2.0, 3.0],
            "model_identifier": "RF-test"
        })
        assert resp.status_code == 200
        assert resp.json()["prediction"] == 42

    def test_missing_body_returns_422(self, client):
        test_client, _ = client
        resp = test_client.post("/api/predict", json={})
        assert resp.status_code == 422


# ── /api/diagnose ────────────────────────────────────────────────────

class TestDiagnoseEndpoint:
    def test_diagnose_with_all_params(self, client):
        test_client, mock_service = client
        mock_service.diagnose_issue.return_value = {
            "diagnosis": "Replace bearing",
            "sources": [{"file": "manual.pdf", "chunk": "bearing...", "search_score": 0.9, "rerank_score": 0.95}],
            "search_method": "hybrid",
            "reranker": "voyage/rerank-2",
            "embedding_model": "voyage/voyage-3",
            "completion_model": "bedrock/nova-lite"
        }
        resp = test_client.get("/api/diagnose", params={
            "issue": "bearing noise",
            "model": "bedrock/nova-lite",
            "reranker": "voyage/rerank-2",
            "embeddings_model": "voyage/voyage-3"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["search_method"] == "hybrid"
        assert len(data["sources"]) == 1

    def test_diagnose_missing_issue_returns_422(self, client):
        test_client, _ = client
        resp = test_client.get("/api/diagnose")
        assert resp.status_code == 422


# ── /api/text_gen ────────────────────────────────────────────────────

class TestTextGenEndpoint:
    def test_text_gen(self, client):
        test_client, mock_service = client
        mock_service.generate_text.return_value = {"answer": "The answer is 42."}
        resp = test_client.get("/api/text_gen", params={
            "text": "What is the meaning of life?",
            "model": "bedrock/nova-lite"
        })
        assert resp.status_code == 200
        assert resp.json()["answer"] == "The answer is 42."


# ── /api/monitoring ──────────────────────────────────────────────────

class TestMonitoringEndpoint:
    def test_monitoring_single_doc(self, client):
        test_client, mock_service = client
        mock_service.get_monitoring_data.return_value = {
            "_id": "abc123",
            "temp": 80,
            "prediction": 1,
            "description": "Normal"
        }
        resp = test_client.get("/api/monitoring", params={
            "sensor": "temp_sensor",
            "limit": 1
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["temp"] == 80

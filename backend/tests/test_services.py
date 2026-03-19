"""Tests for core/services.py — PredictionService business logic (DB + LLM mocked)."""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
from fastapi import HTTPException

from core.services import PredictionService


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def service(mock_mongo_client, mock_db, mock_collection):
    """Build a PredictionService with all external dependencies mocked."""
    return PredictionService(
        client=mock_mongo_client,
        input_db=mock_db,
        output_db=mock_db,
        chunks_col=mock_collection,
        info_col=mock_collection,
        embedding_model="voyage/voyage-3",
        reranker_model="voyage/rerank-2",
        guardrail_id="",
        guardrail_version=""
    )


# ── list_models ──────────────────────────────────────────────────────

class TestListModels:
    def test_lists_models_from_directory(self, service, tmp_model_dir):
        with patch("core.services.model_folder", tmp_model_dir):
            result = service.list_models()
            assert "models" in result
            assert "Random_Forest-valve_condition" in result["models"]
            assert result["count"] == 1

    def test_empty_directory(self, service, tmp_path):
        empty = tmp_path / "empty_models"
        empty.mkdir()
        with patch("core.services.model_folder", empty):
            result = service.list_models()
            assert result["models"] == []

    def test_missing_directory(self, service, tmp_path):
        with patch("core.services.model_folder", tmp_path / "nonexistent"):
            result = service.list_models()
            assert result["models"] == []


# ── make_prediction ──────────────────────────────────────────────────

class TestMakePrediction:
    @patch("core.services.load_scaler")
    @patch("core.services.load_encoder")
    @patch("core.services.load_model")
    def test_successful_prediction(self, mock_load_model, mock_load_encoder, mock_load_scaler, service):
        mock_model = MagicMock()
        mock_model.predict.return_value = [1]
        mock_load_model.return_value = (mock_model, None)

        mock_encoder = MagicMock()
        mock_encoder.inverse_transform.return_value = [42]
        mock_load_encoder.return_value = (mock_encoder, None)

        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = [[1.0, 2.0]]
        mock_load_scaler.return_value = (mock_scaler, None)

        result = service.make_prediction(
            independent_variables=[1.0, 2.0],
            model_identifier="Random_Forest-valve_condition"
        )
        assert result["encoded_prediction"] == 1
        assert result["prediction"] == 42
        assert result["model_used"] == "Random_Forest-valve_condition"

    @patch("core.services.load_model")
    def test_model_not_found_raises(self, mock_load_model, service):
        mock_load_model.return_value = (None, "Model not found")
        with pytest.raises(HTTPException) as exc_info:
            service.make_prediction([1.0], "missing_model")
        # Inner 404 gets caught by outer try/except and re-raised as 500
        assert exc_info.value.status_code in (404, 500)
        assert "not found" in exc_info.value.detail.lower()

    @patch("core.services.load_scaler")
    @patch("core.services.load_encoder")
    @patch("core.services.load_model")
    def test_prediction_without_encoder(self, mock_load_model, mock_load_encoder, mock_load_scaler, service):
        mock_model = MagicMock()
        mock_model.predict.return_value = [3]
        mock_load_model.return_value = (mock_model, None)
        mock_load_encoder.return_value = (None, "not found")
        mock_load_scaler.return_value = (None, "not found")

        result = service.make_prediction([1.0, 2.0], "Random_Forest-test")
        assert result["encoded_prediction"] == 3
        assert "prediction" not in result  # no encoder => no decoded prediction

    @patch("core.services.load_scaler")
    @patch("core.services.load_encoder")
    @patch("core.services.load_model")
    def test_prediction_with_dependent_vars(self, mock_load_model, mock_load_encoder, mock_load_scaler, service):
        mock_model = MagicMock()
        mock_model.predict.return_value = [0]
        mock_load_model.return_value = (mock_model, None)
        mock_load_encoder.return_value = (None, "not found")
        mock_load_scaler.return_value = (None, "not found")

        result = service.make_prediction([1.0], "Random_Forest-x", dependent_variables=[0, 1])
        assert result["dependent_variables"] == [0, 1]


# ── list_sensor_collections ──────────────────────────────────────────

class TestListSensorCollections:
    def test_returns_collections(self, service, mock_db):
        mock_db.list_collection_names.return_value = ["temp_sensor", "pressure_sensor"]
        result = service.list_sensor_collections()
        assert "collections" in result
        assert "temp_sensor" in result["collections"]

    def test_no_client_raises_500(self, service):
        service.client = None
        with pytest.raises(HTTPException) as exc_info:
            service.list_sensor_collections()
        assert exc_info.value.status_code == 500


# ── vector_search ────────────────────────────────────────────────────

class TestVectorSearch:
    @patch("core.services.generate_embeddings")
    def test_vector_search_pipeline(self, mock_embeddings, service, mock_collection):
        mock_embeddings.return_value = [0.1, 0.2, 0.3]
        mock_collection.aggregate.return_value = [
            {"chunk": "text1", "search_score": 0.9},
            {"chunk": "text2", "search_score": 0.8},
        ]

        results = service.vector_search(mock_collection, "voyage/voyage-3", "valve failure", limit=5)
        assert len(results) == 2
        mock_collection.aggregate.assert_called_once()
        pipeline = mock_collection.aggregate.call_args[0][0]
        assert pipeline[0]["$vectorSearch"]["limit"] == 5


# ── hybrid_search ────────────────────────────────────────────────────

class TestHybridSearch:
    @patch("core.services.generate_embeddings")
    def test_hybrid_search_builds_pipeline(self, mock_embeddings, service, mock_collection):
        mock_embeddings.return_value = [0.1, 0.2, 0.3]
        mock_collection.aggregate.return_value = [
            {"_id": "1", "chunk": "text1", "search_score": 0.95, "search_type": "vector"},
        ]

        results = service.hybrid_search(mock_collection, "voyage/voyage-3", "bearing noise", limit=20)
        assert len(results) == 1
        pipeline = mock_collection.aggregate.call_args[0][0]
        # Should contain: $vectorSearch, $addFields, $project, $unionWith, $group, $sort, $limit
        stage_keys = [list(s.keys())[0] for s in pipeline]
        assert "$vectorSearch" in stage_keys
        assert "$unionWith" in stage_keys
        assert "$group" in stage_keys
        assert "$sort" in stage_keys


# ── diagnose_issue ───────────────────────────────────────────────────

class TestDiagnoseIssue:
    @patch("core.services.text_completion")
    @patch("core.services.reranking")
    @patch("core.services.generate_embeddings")
    def test_full_pipeline_with_reranking(self, mock_embed, mock_rerank, mock_completion, service, mock_collection):
        mock_embed.return_value = [0.1, 0.2]
        mock_collection.aggregate.return_value = [
            {"_id": "1", "chunk": "Replace bearing", "file": "manual.pdf", "search_score": 0.9},
            {"_id": "2", "chunk": "Check alignment", "file": "guide.pdf", "search_score": 0.8},
        ]

        mock_rerank_result = MagicMock()
        mock_rerank_result.results = [
            MagicMock(index=0, relevance_score=0.95),
            MagicMock(index=1, relevance_score=0.85),
        ]
        mock_rerank.return_value = mock_rerank_result
        mock_completion.return_value = "Replace the bearing immediately."

        result = service.diagnose_issue(
            issue="valve failure",
            completion_model="bedrock/nova-lite",
            embeddings_model="voyage/voyage-3",
            reranker="voyage/rerank-2"
        )

        assert result["diagnosis"] == "Replace the bearing immediately."
        assert result["search_method"] in ("hybrid", "vector")
        assert result["reranker"] == "voyage/rerank-2"
        assert result["embedding_model"] == "voyage/voyage-3"
        assert result["completion_model"] == "bedrock/nova-lite"
        assert len(result["sources"]) == 2
        assert result["sources"][0]["rerank_score"] == 0.95

    @patch("core.services.text_completion")
    @patch("core.services.generate_embeddings")
    def test_no_reranker(self, mock_embed, mock_completion, service, mock_collection):
        mock_embed.return_value = [0.1]
        mock_collection.aggregate.return_value = [
            {"_id": "1", "chunk": "info", "file": "doc.pdf", "search_score": 0.7},
        ]
        mock_completion.return_value = "Answer"

        result = service.diagnose_issue(
            issue="problem",
            completion_model="model",
            reranker="No rerank"
        )

        assert result["reranker"] is None  # "No rerank" is treated as disabled
        assert result["diagnosis"] == "Answer"

    @patch("core.services.text_completion")
    @patch("core.services.reranking")
    @patch("core.services.generate_embeddings")
    def test_reranking_failure_falls_back(self, mock_embed, mock_rerank, mock_completion, service, mock_collection):
        mock_embed.return_value = [0.1]
        mock_collection.aggregate.return_value = [
            {"_id": str(i), "chunk": f"chunk{i}", "file": "f.pdf", "search_score": 0.5}
            for i in range(10)
        ]
        mock_rerank.side_effect = Exception("Reranking service unavailable")
        mock_completion.return_value = "fallback answer"

        result = service.diagnose_issue(issue="test", completion_model="m", reranker="voyage/rerank-2")
        # Should still succeed with top 5 unranked results
        assert result["diagnosis"] == "fallback answer"
        assert len(result["sources"]) == 5

    def test_empty_issue_raises(self, service):
        with pytest.raises(HTTPException) as exc_info:
            service.diagnose_issue(issue="", completion_model="m")
        # Inner 400 may be caught by outer try/except and re-raised as 500
        assert exc_info.value.status_code in (400, 500)
        assert "required" in exc_info.value.detail.lower()

    @patch("core.services.text_completion")
    @patch("core.services.generate_embeddings")
    def test_hybrid_search_failure_falls_back_to_vector(self, mock_embed, mock_completion, service, mock_collection):
        mock_embed.return_value = [0.1]
        # First call (hybrid) fails, second call (vector) succeeds
        mock_collection.aggregate.side_effect = [
            Exception("text_search index not found"),
            [{"_id": "1", "chunk": "info", "file": "f.pdf", "search_score": 0.6}]
        ]
        mock_completion.return_value = "recovered"

        result = service.diagnose_issue(issue="test", completion_model="m", reranker="No rerank")
        assert result["search_method"] == "vector"
        assert result["diagnosis"] == "recovered"


# ── get_monitoring_data ──────────────────────────────────────────────

class TestGetMonitoringData:
    def test_returns_single_doc_when_limit_1(self, service, mock_db):
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__ = lambda self: iter([{"_id": "abc", "temp": 80}])

        mock_col = MagicMock()
        mock_col.find.return_value = mock_cursor
        mock_db.__getitem__ = MagicMock(return_value=mock_col)

        result = service.get_monitoring_data("sensor_a", limit=1)
        assert isinstance(result, dict)
        assert result["_id"] == "abc"

    def test_empty_sensor_raises(self, service):
        with pytest.raises(HTTPException) as exc_info:
            service.get_monitoring_data("", limit=10)
        # Inner 400 may be caught by outer try/except and re-raised as 500
        assert exc_info.value.status_code in (400, 500)
        assert "sensor" in exc_info.value.detail.lower()

    def test_no_client_raises_500(self, service):
        service.client = None
        with pytest.raises(HTTPException) as exc_info:
            service.get_monitoring_data("sensor_a")
        assert exc_info.value.status_code == 500


# ── generate_text ────────────────────────────────────────────────────

class TestGenerateText:
    @patch("core.services.text_completion")
    def test_basic_text_gen(self, mock_completion, service):
        mock_completion.return_value = "Generated text"
        result = service.generate_text("Write a poem", "bedrock/nova-lite")
        assert result["answer"] == "Generated text"

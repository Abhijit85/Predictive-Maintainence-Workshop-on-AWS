"""Tests for utils/llm_utils.py — LiteLLM wrapper functions (all external calls mocked)."""

import json
import pytest
from unittest.mock import patch, MagicMock

from utils.llm_utils import text_completion, generate_embeddings, reranking


# ── text_completion ──────────────────────────────────────────────────

class TestTextCompletion:
    @patch("utils.llm_utils.completion")
    def test_basic_call(self, mock_completion):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "42 degrees"}}]
        }
        mock_completion.return_value = mock_resp

        result = text_completion("bedrock/nova-lite", "What temp?")
        assert result == "42 degrees"
        mock_completion.assert_called_once()
        call_kwargs = mock_completion.call_args[1]
        assert call_kwargs["model"] == "bedrock/nova-lite"
        assert "extra_headers" not in call_kwargs

    @patch("utils.llm_utils.completion")
    def test_with_guardrails(self, mock_completion):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "safe answer"}}]
        }
        mock_completion.return_value = mock_resp

        result = text_completion(
            "model", "prompt",
            guardrail_id="gr-abc",
            guardrail_version="1"
        )
        assert result == "safe answer"
        call_kwargs = mock_completion.call_args[1]
        assert "extra_headers" in call_kwargs
        assert call_kwargs["extra_headers"]["X-Amzn-Bedrock-GuardrailIdentifier"] == "gr-abc"
        assert call_kwargs["extra_headers"]["X-Amzn-Bedrock-GuardrailVersion"] == "1"

    @patch("utils.llm_utils.completion")
    def test_no_guardrails_when_id_empty(self, mock_completion):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_completion.return_value = mock_resp

        text_completion("model", "prompt", guardrail_id="", guardrail_version="1")
        call_kwargs = mock_completion.call_args[1]
        assert "extra_headers" not in call_kwargs

    @patch("utils.llm_utils.completion")
    def test_no_guardrails_when_version_none(self, mock_completion):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }
        mock_completion.return_value = mock_resp

        text_completion("model", "prompt", guardrail_id="gr-1", guardrail_version=None)
        call_kwargs = mock_completion.call_args[1]
        assert "extra_headers" not in call_kwargs


# ── generate_embeddings ──────────────────────────────────────────────

class TestGenerateEmbeddings:
    @patch("utils.llm_utils.embedding")
    def test_returns_embedding_vector(self, mock_embedding):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }
        mock_embedding.return_value = mock_resp

        result = generate_embeddings("voyage/voyage-3", "test query")
        assert result == [0.1, 0.2, 0.3]
        mock_embedding.assert_called_once_with(model="voyage/voyage-3", input=["test query"])


# ── reranking ────────────────────────────────────────────────────────

class TestReranking:
    @patch("utils.llm_utils.rerank")
    def test_basic_rerank(self, mock_rerank):
        mock_resp = MagicMock()
        mock_resp.results = [
            MagicMock(index=1, relevance_score=0.95),
            MagicMock(index=0, relevance_score=0.80),
        ]
        mock_rerank.return_value = mock_resp

        result = reranking("voyage/rerank-2", "query", ["doc1", "doc2"], top_n=2)
        assert len(result.results) == 2
        mock_rerank.assert_called_once_with(
            model="voyage/rerank-2",
            query="query",
            documents=["doc1", "doc2"],
            top_n=2
        )

    @patch("utils.llm_utils.rerank")
    def test_top_n_defaults_to_doc_count(self, mock_rerank):
        mock_rerank.return_value = MagicMock(results=[])
        reranking("model", "query", ["a", "b", "c"])
        call_kwargs = mock_rerank.call_args[1]
        assert call_kwargs["top_n"] == 3

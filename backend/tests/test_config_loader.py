"""Tests for config/config_loader.py — env var resolution, YAML loading, config classes."""

import os
import pytest
from unittest.mock import patch, MagicMock

from config.config_loader import (
    resolve_env_variables,
    load_yaml_config,
    ConfigurationError,
    FastAPIConfig,
    ModelsConfig,
    StreamingConfig,
)


# ── resolve_env_variables ────────────────────────────────────────────

class TestResolveEnvVariables:
    def test_plain_string_unchanged(self):
        assert resolve_env_variables("hello") == "hello"

    def test_simple_env_var(self, monkeypatch):
        monkeypatch.setenv("MY_VAR", "resolved")
        assert resolve_env_variables("${MY_VAR}") == "resolved"

    def test_env_var_with_default_uses_env(self, monkeypatch):
        monkeypatch.setenv("MY_VAR", "from_env")
        assert resolve_env_variables("${MY_VAR:-fallback}") == "from_env"

    def test_env_var_with_default_falls_back(self, monkeypatch):
        monkeypatch.delenv("MISSING_VAR", raising=False)
        assert resolve_env_variables("${MISSING_VAR:-fallback}") == "fallback"

    def test_missing_env_var_no_default_raises(self, monkeypatch):
        monkeypatch.delenv("TOTALLY_MISSING", raising=False)
        with pytest.raises(ConfigurationError, match="TOTALLY_MISSING"):
            resolve_env_variables("${TOTALLY_MISSING}")

    def test_nested_dict(self, monkeypatch):
        monkeypatch.setenv("DB_HOST", "mongo.local")
        data = {"database": {"host": "${DB_HOST:-localhost}"}}
        result = resolve_env_variables(data)
        assert result["database"]["host"] == "mongo.local"

    def test_list_resolution(self, monkeypatch):
        monkeypatch.setenv("ITEM", "x")
        result = resolve_env_variables(["${ITEM}", "literal"])
        assert result == ["x", "literal"]

    def test_non_string_passthrough(self):
        assert resolve_env_variables(42) == 42
        assert resolve_env_variables(None) is None
        assert resolve_env_variables(True) is True

    def test_empty_default(self, monkeypatch):
        monkeypatch.delenv("OPT_VAR", raising=False)
        assert resolve_env_variables("${OPT_VAR:-}") == ""

    def test_multiple_vars_in_one_string(self, monkeypatch):
        monkeypatch.setenv("A", "hello")
        monkeypatch.setenv("B", "world")
        assert resolve_env_variables("${A} ${B}") == "hello world"


# ── load_yaml_config ─────────────────────────────────────────────────

class TestLoadYamlConfig:
    def test_default_config_loads(self):
        """The project's config.yaml should load without error."""
        config = load_yaml_config()
        assert config is not None
        assert "server" in config
        assert "database" in config
        assert "embeddings" in config
        assert "reranker" in config
        assert "guardrails" in config
        assert "alerts" in config

    def test_missing_file_returns_none(self, tmp_path):
        result = load_yaml_config(str(tmp_path / "nope.yaml"))
        assert result is None

    def test_custom_path(self, tmp_path):
        cfg_file = tmp_path / "test.yaml"
        cfg_file.write_text("key: value\n")
        result = load_yaml_config(str(cfg_file))
        assert result == {"key": "value"}


# ── FastAPIConfig ────────────────────────────────────────────────────

class TestFastAPIConfig:
    def test_defaults_loaded(self):
        cfg = FastAPIConfig()
        assert cfg.HOST == "127.0.0.1"
        assert cfg.PORT == 5001
        assert cfg.RELOAD is False
        assert cfg.EMBEDDING_MODEL == "voyage/voyage-3"
        assert cfg.RERANKER_MODEL == "voyage/rerank-2"
        assert cfg.BEDROCK_GUARDRAIL_ID == ""
        assert cfg.BEDROCK_GUARDRAIL_VERSION == ""
        assert cfg.SNS_ALERT_TOPIC_ARN == ""

    def test_env_override_host(self, monkeypatch):
        monkeypatch.setenv("REACT_APP_FASTAPI_HOST", "0.0.0.0")
        cfg = FastAPIConfig()
        assert cfg.HOST == "0.0.0.0"

    def test_env_override_embedding_model(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_MODEL", "bedrock/amazon.titan-embed-text-v2:0")
        cfg = FastAPIConfig()
        assert cfg.EMBEDDING_MODEL == "bedrock/amazon.titan-embed-text-v2:0"

    def test_env_override_reranker(self, monkeypatch):
        monkeypatch.setenv("RERANKER_MODEL", "custom/reranker-v1")
        cfg = FastAPIConfig()
        assert cfg.RERANKER_MODEL == "custom/reranker-v1"

    def test_env_override_guardrails(self, monkeypatch):
        monkeypatch.setenv("BEDROCK_GUARDRAIL_ID", "gr-123")
        monkeypatch.setenv("BEDROCK_GUARDRAIL_VERSION", "1")
        cfg = FastAPIConfig()
        assert cfg.BEDROCK_GUARDRAIL_ID == "gr-123"
        assert cfg.BEDROCK_GUARDRAIL_VERSION == "1"

    def test_env_override_sns(self, monkeypatch):
        monkeypatch.setenv("SNS_ALERT_TOPIC_ARN", "arn:aws:sns:us-east-1:123456:alerts")
        cfg = FastAPIConfig()
        assert cfg.SNS_ALERT_TOPIC_ARN == "arn:aws:sns:us-east-1:123456:alerts"

    def test_collections_loaded(self):
        cfg = FastAPIConfig()
        assert cfg.INPUT_DB  # non-empty
        assert cfg.OUTPUT_DB
        assert cfg.CHUNKS_COL
        assert cfg.INFO_COL

    def test_log_configuration_runs(self, capsys):
        cfg = FastAPIConfig()
        cfg.log_configuration()  # should not raise


# ── ModelsConfig ─────────────────────────────────────────────────────

class TestModelsConfig:
    def test_defaults_loaded(self):
        cfg = ModelsConfig()
        assert cfg.TEST_SIZE == 0.3
        assert cfg.RANDOM_STATE == 42
        assert "models" in cfg.MODEL_FOLDER
        assert "encoders" in cfg.ENCODER_FOLDER
        assert "datasets" in cfg.DATASET_FOLDER


# ── StreamingConfig ──────────────────────────────────────────────────

class TestStreamingConfig:
    def test_defaults_loaded(self):
        cfg = StreamingConfig()
        assert cfg.HOST == "127.0.0.1"
        assert cfg.PORT == 5001
        assert cfg.SNS_ALERT_TOPIC_ARN == ""

    def test_env_override_sns(self, monkeypatch):
        monkeypatch.setenv("SNS_ALERT_TOPIC_ARN", "arn:aws:sns:us-east-1:123:topic")
        cfg = StreamingConfig()
        assert cfg.SNS_ALERT_TOPIC_ARN == "arn:aws:sns:us-east-1:123:topic"

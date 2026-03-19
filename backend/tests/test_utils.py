"""Tests for utils/utils.py — model loading, validation, and model name resolution."""

import pickle
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── validate_input_data ──────────────────────────────────────────────

class TestValidateInputData:
    """Test validate_input_data without importing module-level config globals."""

    @pytest.fixture(autouse=True)
    def _import_validate(self):
        from utils.utils import validate_input_data
        self.validate = validate_input_data

    def test_valid_data(self):
        data = {
            "independent_variables": [1.0, 2.0],
            "model_identifier": "model_a"
        }
        ok, err = self.validate(data)
        assert ok is True
        assert err is None

    def test_not_a_dict(self):
        ok, err = self.validate("not a dict")
        assert ok is False
        assert "dictionary" in err

    def test_missing_independent_variables(self):
        ok, err = self.validate({"model_identifier": "m"})
        assert ok is False
        assert "independent_variables" in err

    def test_missing_model_identifier(self):
        ok, err = self.validate({"independent_variables": [1.0]})
        assert ok is False
        assert "model_identifier" in err

    def test_independent_variables_not_list(self):
        ok, err = self.validate({
            "independent_variables": "not a list",
            "model_identifier": "m"
        })
        assert ok is False
        assert "list" in err

    def test_empty_independent_variables(self):
        ok, err = self.validate({
            "independent_variables": [],
            "model_identifier": "m"
        })
        assert ok is False
        assert "empty" in err


# ── load_model ───────────────────────────────────────────────────────

class TestLoadModel:
    def test_load_existing_model(self, tmp_model_dir):
        with patch("utils.utils.model_folder", str(tmp_model_dir)):
            from utils.utils import load_model
            model, err = load_model("Random_Forest-valve_condition")
            assert model is not None
            assert err is None

    def test_load_missing_model(self, tmp_model_dir):
        with patch("utils.utils.model_folder", str(tmp_model_dir)):
            from utils.utils import load_model
            model, err = load_model("Nonexistent_Model")
            assert model is None
            assert "not found" in err


# ── load_encoder / load_scaler ───────────────────────────────────────

class TestLoadEncoderAndScaler:
    def test_load_existing_encoder(self, tmp_encoder_dir):
        with patch("utils.utils.encoder_folder", str(tmp_encoder_dir)):
            from utils.utils import load_encoder
            enc, err = load_encoder("valve_condition")
            assert enc is not None
            assert err is None

    def test_load_missing_encoder(self, tmp_encoder_dir):
        with patch("utils.utils.encoder_folder", str(tmp_encoder_dir)):
            from utils.utils import load_encoder
            enc, err = load_encoder("nonexistent")
            assert enc is None
            assert "not found" in err

    def test_load_existing_scaler(self, tmp_encoder_dir):
        with patch("utils.utils.encoder_folder", str(tmp_encoder_dir)):
            from utils.utils import load_scaler
            scaler, err = load_scaler("valve_condition")
            assert scaler is not None
            assert err is None

    def test_load_missing_scaler(self, tmp_encoder_dir):
        with patch("utils.utils.encoder_folder", str(tmp_encoder_dir)):
            from utils.utils import load_scaler
            scaler, err = load_scaler("nonexistent")
            assert scaler is None
            assert "not found" in err


# ── get_model_name ───────────────────────────────────────────────────

class TestGetModelName:
    def test_exact_match(self, tmp_model_dir):
        with patch("utils.utils.model_folder", str(tmp_model_dir)):
            from utils.utils import get_model_name
            result = get_model_name("valve_condition")
            assert result == "Random_Forest-valve_condition"

    def test_case_insensitive_match(self, tmp_model_dir):
        with patch("utils.utils.model_folder", str(tmp_model_dir)):
            from utils.utils import get_model_name
            result = get_model_name("Valve_Condition")
            assert result == "Random_Forest-valve_condition"

    def test_no_match(self, tmp_model_dir):
        with patch("utils.utils.model_folder", str(tmp_model_dir)):
            from utils.utils import get_model_name
            result = get_model_name("totally_unknown")
            assert result is None

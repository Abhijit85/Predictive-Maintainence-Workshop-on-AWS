"""Shared fixtures for the test suite."""

import os
import sys
import pytest
import pickle
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Ensure tests don't leak environment variables."""
    monkeypatch.setenv("MONGODB_URI", "mongodb://testhost:27017")


# ── Picklable stub classes (MagicMock can't be pickled) ──────────────

class StubModel:
    """A picklable stand-in for a sklearn model."""
    def predict(self, X):
        return np.array([1])


class StubEncoder:
    """A picklable stand-in for a sklearn LabelEncoder."""
    def inverse_transform(self, y):
        return np.array([42])


class StubScaler:
    """A picklable stand-in for a sklearn StandardScaler."""
    def transform(self, X):
        return np.array([[1.0, 2.0, 3.0]])


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def tmp_model_dir(tmp_path):
    """Create a temporary models directory with a dummy sklearn model."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    with open(models_dir / "Random_Forest-valve_condition.pkl", "wb") as f:
        pickle.dump(StubModel(), f)
    return models_dir


@pytest.fixture
def tmp_encoder_dir(tmp_path):
    """Create a temporary encoders directory with dummy encoder + scaler."""
    encoders_dir = tmp_path / "encoders"
    encoders_dir.mkdir()
    with open(encoders_dir / "valve_condition.pkl", "wb") as f:
        pickle.dump(StubEncoder(), f)
    with open(encoders_dir / "valve_condition_scaler.pkl", "wb") as f:
        pickle.dump(StubScaler(), f)
    return encoders_dir


@pytest.fixture
def mock_mongo_client():
    """Return a MagicMock that behaves like a MongoClient."""
    client = MagicMock()
    client.admin.command.return_value = {"ok": 1}
    return client


@pytest.fixture
def mock_db():
    """Return a MagicMock that behaves like a MongoDB Database."""
    db = MagicMock()
    db.list_collection_names.return_value = ["sensor_a", "sensor_b"]
    return db


@pytest.fixture
def mock_collection():
    """Return a MagicMock that behaves like a MongoDB Collection."""
    col = MagicMock()
    col.name = "chunks"
    col.aggregate.return_value = []
    return col

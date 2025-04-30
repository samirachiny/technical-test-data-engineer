import os
import json
import tempfile
import pytest
import requests
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from moovitamix_fastapi import client_pipeline
from moovitamix_fastapi.client_pipeline import (
    fetch_data,
    validate_items,
    save_to_json,
    notify_failure,
    SCHEMA_BY_ENDPOINT,
    MAX_RETRIES
)

# ========== TEST FETCH ==========

@patch("moovitamix_fastapi.client_pipeline.requests.get")
def test_fetch_data_success(mock_get):
    """Teste la récupération réussie de données"""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"items": []}
    data = fetch_data("tracks")
    assert isinstance(data, dict)
    assert "items" in data

@patch("time.sleep")
@patch("moovitamix_fastapi.client_pipeline.requests.get")
def test_fetch_data_retry(mock_get, mock_sleep):
    """Teste le mécanisme de réessai"""
    mock_get.side_effect = requests.exceptions.ConnectionError()
    result = fetch_data("tracks")
    assert result is None
    assert mock_get.call_count == MAX_RETRIES

# ========== TEST VALIDATION ==========

def test_validate_items_valid():
    """Teste la validation avec des données valides"""
    with patch.dict(SCHEMA_BY_ENDPOINT, {"tracks": MagicMock()}):
        assert validate_items("tracks", {"items": [{}]}) is True

def test_validate_items_invalid():
    with patch.dict(SCHEMA_BY_ENDPOINT, {"tracks": MagicMock()}):
        mock_schema = SCHEMA_BY_ENDPOINT["tracks"]
        mock_schema.side_effect = ValidationError.from_exception_data(
            title="Validation Error",
            line_errors=[]
        )
        assert validate_items("tracks", {"items": [{}]}) is False

# ========== TEST SAUVEGARDE ==========

def test_save_to_json_creates_file():
    """Vérifie la création correcte des fichiers"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Sauvegarde temporaire
        original_dir = client_pipeline.DATA_DIR
        client_pipeline.DATA_DIR = tmpdir
        
        # Test
        test_data = {"key": "value"}
        save_to_json(test_data, "test.json")
        
        # Vérifications
        path = os.path.join(tmpdir, "test.json")
        assert os.path.exists(path)
        with open(path, "r") as f:
            assert json.load(f) == test_data
        
        # Nettoyage
        client_pipeline.DATA_DIR = original_dir
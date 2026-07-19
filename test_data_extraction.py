import importlib

import pytest


def test_data_extraction_import_does_not_require_youtube_key(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)

    module = importlib.import_module("src.data_extraction")

    with pytest.raises(ValueError, match="YouTube API key not found"):
        module.get_youtube_api_key()


def test_data_extraction_reads_youtube_key_when_needed(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")
    module = importlib.import_module("src.data_extraction")

    assert module.get_youtube_api_key() == "test-key"

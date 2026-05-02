"""Tests for the word_of_day plugin."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from plugins.word_of_day import WordOfDayPlugin
from src.plugins.base import PluginResult

MANIFEST = json.loads("""
{
    "id": "word_of_day",
    "name": "Word of the Day",
    "version": "0.1.0",
    "settings_schema": {
        "type": "object",
        "properties": {
            "enabled": {
                "type": "boolean",
                "title": "Enabled",
                "default": false
            },
            "custom_word": {
                "type": "string",
                "title": "Custom Word",
                "description": "Leave blank to show a daily word from the built-in list, or enter a word to always show.",
                "default": ""
            },
            "refresh_seconds": {
                "type": "integer",
                "title": "Refresh Interval (seconds)",
                "description": "How often to refresh (once per day is sufficient).",
                "default": 3600,
                "minimum": 3600
            }
        },
        "required": []
    }
}
""")

SAMPLE_RESPONSE = json.loads("""
[
    {
        "word": "ephemeral",
        "phonetic": "/\u026a\u02c8fem(\u0259)r(\u0259)l/",
        "meanings": [
            {
                "partOfSpeech": "adjective",
                "definitions": [
                    {
                        "definition": "lasting for a very short time",
                        "example": "fashions are ephemeral"
                    }
                ]
            }
        ]
    }
]
""")


@pytest.fixture
def plugin():
    return WordOfDayPlugin(MANIFEST)


@pytest.fixture
def configured_plugin():
    p = WordOfDayPlugin(MANIFEST)
    p.config = json.loads("""
{
    "custom_word": ""
}
""")
    return p


class TestWordOfDayPlugin:

    def test_plugin_id(self, plugin):
        assert plugin.plugin_id == "word_of_day"

    def test_manifest_valid(self):
        manifest_path = Path(__file__).parent.parent / "manifest.json"
        with open(manifest_path) as f:
            m = json.load(f)
        for field in ("id", "name", "version"):
            assert field in m

    @patch("plugins.word_of_day.requests.get")
    def test_fetch_data_success(self, mock_get, configured_plugin):
        mock_response = Mock()
        mock_response.json.return_value = SAMPLE_RESPONSE
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = configured_plugin.fetch_data()

        assert result.available is True
        assert result.error is None
        assert result.data is not None
        assert "word" in result.data, "missing variable: word"
        assert "part_of_speech" in result.data, "missing variable: part_of_speech"
        assert "definition" in result.data, "missing variable: definition"
        assert "phonetic" in result.data, "missing variable: phonetic"

    @patch("plugins.word_of_day.requests.get")
    def test_fetch_data_network_error(self, mock_get, configured_plugin):
        import requests as req_mod
        mock_get.side_effect = req_mod.exceptions.ConnectionError("network down")

        result = configured_plugin.fetch_data()

        assert result.available is False
        assert result.error is not None

    @patch("plugins.word_of_day.requests.get")
    def test_fetch_data_bad_json(self, mock_get, configured_plugin):
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("bad json")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = configured_plugin.fetch_data()

        assert result.available is False


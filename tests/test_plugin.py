"""Tests for the word_of_day plugin."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from word_of_day import WordOfDayPlugin
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
{
    "en": [
        {
            "partOfSpeech": "Adjective",
            "language": "English",
            "definitions": [
                {
                    "definition": "Lasting for a <a rel=\\"mw:WikiLink\\" href=\\"/wiki/short\\">short</a> period of time."
                }
            ]
        }
    ]
}
""")

SAMPLE_WIKITEXT = json.loads("""
{
    "query": {
        "pages": {
            "123": {
                "revisions": [
                    {"slots": {"main": {"*": "==English==\\n* {{IPA|en|/\\u025b\\u02c8f\\u025b.m\\u0259.\\u0279\\u0259l/}}\\n==Dutch==\\n* {{IPA|nl|/xxx/}}"}}}
                ]
            }
        }
    }
}
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


def _router(definition=SAMPLE_RESPONSE, wikitext=SAMPLE_WIKITEXT, definition_error=None):
    """Route the two lookups the plugin makes to their own mock responses."""

    def _get(url, **kwargs):
        if "rest_v1/page/definition" in url:
            if definition_error is not None:
                raise definition_error
            payload = definition
        else:
            payload = wikitext
        response = Mock()
        response.json.return_value = payload
        response.raise_for_status = Mock()
        return response

    return _get


class TestWordOfDayPlugin:

    def test_plugin_id(self, plugin):
        assert plugin.plugin_id == "word_of_day"

    def test_manifest_valid(self):
        manifest_path = Path(__file__).parent.parent / "manifest.json"
        with open(manifest_path) as f:
            m = json.load(f)
        for field in ("id", "name", "version"):
            assert field in m

    @patch("word_of_day.requests.get")
    def test_fetch_data_success(self, mock_get, configured_plugin):
        mock_get.side_effect = _router()

        result = configured_plugin.fetch_data()

        assert result.available is True
        assert result.error is None
        assert result.data is not None
        for variable in (
            "word",
            "part_of_speech",
            "definition",
            "phonetic",
            "translation_es",
            "translation_it",
            "translation_ja",
            "translation_de",
            "translation_fr",
            "translation_la",
        ):
            assert variable in result.data, f"missing variable: {variable}"

    @patch("word_of_day.requests.get")
    def test_definition_is_plain_text(self, mock_get, configured_plugin):
        """Wiktionary markup must not reach the board."""
        mock_get.side_effect = _router()

        data = configured_plugin.fetch_data().data

        assert data["definition"] == "Lasting for a short period of time."
        assert data["part_of_speech"] == "adjective"

    @patch("word_of_day.requests.get")
    def test_phonetic_comes_from_the_english_section(self, mock_get, configured_plugin):
        mock_get.side_effect = _router()

        assert configured_plugin.fetch_data().data["phonetic"] == "/\u025b\u02c8f\u025b.m\u0259.\u0279\u0259l/"

    @patch("word_of_day.requests.get")
    def test_fetch_data_network_error(self, mock_get, configured_plugin):
        """A dictionary outage must not blank the board.

        Regression test: the plugin used to report ``available=False`` when the
        lookup failed, which rendered every merge field as "???" even though the
        word and its translations are local data that needs no network at all.
        """
        import requests as req_mod
        mock_get.side_effect = req_mod.exceptions.ConnectionError("network down")

        result = configured_plugin.fetch_data()

        assert result.available is True
        assert result.data["word"]
        assert result.data["translation_es"]
        assert result.data["definition"] == ""
        assert result.data["part_of_speech"] == ""
        assert result.data["phonetic"] == ""

    @patch("word_of_day.requests.get")
    def test_fetch_data_bad_json(self, mock_get, configured_plugin):
        mock_get.side_effect = _router(definition_error=ValueError("bad json"))

        result = configured_plugin.fetch_data()

        assert result.available is True
        assert result.data["word"]
        assert result.data["definition"] == ""

    @patch("word_of_day.requests.get")
    def test_non_english_sections_are_skipped(self, mock_get, configured_plugin):
        """The "en" payload also carries non-English entries; skip them."""
        payload = {
            "en": [
                {
                    "partOfSpeech": "Symbol",
                    "language": "Translingual",
                    "definitions": [{"definition": "ISO 639-2 code."}],
                },
                {
                    "partOfSpeech": "Verb",
                    "language": "English",
                    "definitions": [{"definition": "To move swiftly."}],
                },
            ]
        }
        mock_get.side_effect = _router(definition=payload)

        data = configured_plugin.fetch_data().data

        assert data["definition"] == "To move swiftly."
        assert data["part_of_speech"] == "verb"

    @patch("word_of_day.requests.get")
    def test_inline_stylesheets_are_stripped(self, mock_get, configured_plugin):
        """Some entries carry a <style> block whose CSS survives tag stripping."""
        payload = {
            "en": [
                {
                    "partOfSpeech": "Adjective",
                    "language": "English",
                    "definitions": [
                        {
                            "definition": (
                                "Differing from the norm."
                                "<style>.mw-parser-output .defdate{font-size:smaller}</style>"
                            )
                        }
                    ],
                }
            ]
        }
        mock_get.side_effect = _router(definition=payload)

        assert configured_plugin.fetch_data().data["definition"] == "Differing from the norm."

    @patch("word_of_day.requests.get")
    def test_sub_senses_are_dropped(self, mock_get, configured_plugin):
        """Only the leading gloss is kept; nested <ol> sub-senses are not."""
        payload = {
            "en": [
                {
                    "partOfSpeech": "Verb",
                    "language": "English",
                    "definitions": [
                        {"definition": "To move swiftly.\n<ol><li>To move quickly on foot.</li></ol>"}
                    ],
                }
            ]
        }
        mock_get.side_effect = _router(definition=payload)

        assert configured_plugin.fetch_data().data["definition"] == "To move swiftly."

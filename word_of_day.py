"""Display a word, its pronunciation, definition, and translations."""

from __future__ import annotations

import datetime
import html
import logging
import re
from typing import Any, Dict, List, Tuple

import requests

from src.plugins.base import PluginBase, PluginResult
from words import WORD_LIST

logger = logging.getLogger(__name__)

USER_AGENT = "FiestaBoard Word of the Day Plugin (https://github.com/Fiestaboard/fiestaboard-plugin--word-of-day)"

DEFINITION_URL = "https://en.wiktionary.org/api/rest_v1/page/definition/{word}"
WIKITEXT_URL = "https://en.wiktionary.org/w/api.php"

_WORD_INDEX = {entry["word"]: entry for entry in WORD_LIST}

# Wiktionary hands back definitions as HTML fragments: links, formatting, an
# occasional inline <style> block, and sub-senses nested in a trailing <ol>.
# Only the leading gloss is wanted, as plain text.
_SUBSENSES_RE = re.compile(r"<ol\b", re.I)
_STYLE_RE = re.compile(r"<(style|script)\b[^>]*>.*?</\1>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

# Pronunciation lives in the page wikitext, not in the definition endpoint.
_ENGLISH_SECTION_RE = re.compile(r"==\s*English\s*==(.*?)(?=\n==[^=]|\Z)", re.S)
_IPA_RE = re.compile(r"\{\{IPA\|en\|([^}|]+)")


def _clean_definition(fragment: str) -> str:
    """Reduce one Wiktionary definition fragment to plain text."""
    fragment = _SUBSENSES_RE.split(fragment, maxsplit=1)[0]
    fragment = _STYLE_RE.sub("", fragment)
    return _WS_RE.sub(" ", html.unescape(_TAG_RE.sub("", fragment))).strip()


def _extract_definition(payload: Any) -> Tuple[str, str]:
    """Pull the first English (part of speech, definition) pair from a payload.

    The ``en`` key holds every section of the English *Wiktionary* page, which
    includes non-English entries — "run" leads with a Translingual symbol — so
    sections are filtered on their language rather than trusted by position.
    """
    if not isinstance(payload, dict):
        return "", ""
    for section in payload.get("en", []):
        if not isinstance(section, dict) or section.get("language") != "English":
            continue
        for definition in section.get("definitions", []):
            text = _clean_definition(str(definition.get("definition", "")))
            if text:
                return str(section.get("partOfSpeech", "")).lower(), text
    return "", ""


def _fetch_definition(word: str) -> Tuple[str, str]:
    """Look up a word's part of speech and definition. Raises on failure."""
    response = requests.get(
        DEFINITION_URL.format(word=word),
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    return _extract_definition(response.json())


def _fetch_phonetic(word: str) -> str:
    """Best-effort IPA lookup; returns "" rather than raising."""
    try:
        response = requests.get(
            WIKITEXT_URL,
            params={
                "action": "query",
                "prop": "revisions",
                "rvprop": "content",
                "rvslots": "main",
                "format": "json",
                "titles": word,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        pages = response.json()["query"]["pages"]
        content = next(iter(pages.values()))["revisions"][0]["slots"]["main"]["*"]
        english = _ENGLISH_SECTION_RE.search(content)
        match = _IPA_RE.search(english.group(1) if english else content)
        return match.group(1).strip() if match else ""
    except Exception as e:
        logger.debug("Phonetic lookup failed for '%s': %s", word, e)
        return ""


class WordOfDayPlugin(PluginBase):
    """Word of the Day plugin for FiestaBoard."""

    @property
    def plugin_id(self) -> str:
        return "word_of_day"

    def fetch_data(self) -> PluginResult:
        try:
            custom_word = (self.config.get("custom_word") or "").strip().lower()
            if custom_word:
                word = custom_word
                word_entry = _WORD_INDEX.get(custom_word)
            else:
                day_of_year = datetime.date.today().timetuple().tm_yday
                word_entry = WORD_LIST[(day_of_year - 1) % len(WORD_LIST)]
                word = word_entry["word"]

            # The word and its translations are local data. Keeping them
            # independent of the lookup means a dictionary outage costs the
            # definition only, instead of blanking every variable on the board.
            data: Dict[str, Any] = {
                "word": word,
                "part_of_speech": "",
                "definition": "",
                "phonetic": "",
                "translation_es": word_entry["es"] if word_entry else "",
                "translation_it": word_entry["it"] if word_entry else "",
                "translation_ja": word_entry["ja"] if word_entry else "",
                "translation_de": word_entry["de"] if word_entry else "",
                "translation_fr": word_entry["fr"] if word_entry else "",
                "translation_la": word_entry["la"] if word_entry else "",
            }

            try:
                part_of_speech, definition = _fetch_definition(word)
                data["part_of_speech"] = part_of_speech
                data["definition"] = definition
            except Exception as e:
                logger.warning("Definition lookup failed for '%s': %s", word, e)

            data["phonetic"] = _fetch_phonetic(word)

            return PluginResult(available=True, data=data)
        except Exception as e:
            logger.exception("Error fetching word of the day")
            return PluginResult(available=False, error=str(e))

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []

    def cleanup(self) -> None:
        pass


Plugin = WordOfDayPlugin

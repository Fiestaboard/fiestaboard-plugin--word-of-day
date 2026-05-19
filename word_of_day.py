"""Display a word, its pronunciation, definition, and translations."""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, List

import requests

from src.plugins.base import PluginBase, PluginResult
from words import WORD_LIST

logger = logging.getLogger(__name__)

USER_AGENT = "FiestaBoard Word of the Day Plugin (https://github.com/Fiestaboard/fiestaboard-plugin--word-of-day)"

_WORD_INDEX = {entry["word"]: entry for entry in WORD_LIST}


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

            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=10,
            )
            response.raise_for_status()
            entries = response.json()

            if not entries or not isinstance(entries, list):
                return PluginResult(available=False, error=f"No definition found for '{word}'")

            entry = entries[0]
            phonetic = str(entry.get("phonetic", ""))[:15]
            meanings = entry.get("meanings", [])
            part_of_speech = ""
            definition = ""
            if meanings:
                meaning = meanings[0]
                part_of_speech = str(meaning.get("partOfSpeech", ""))[:12]
                defs = meaning.get("definitions", [])
                if defs:
                    definition = str(defs[0].get("definition", ""))

            data: Dict[str, Any] = {
                "word": word,
                "part_of_speech": part_of_speech,
                "definition": definition,
                "phonetic": phonetic,
                "translation_es": word_entry["es"] if word_entry else "",
                "translation_it": word_entry["it"] if word_entry else "",
                "translation_ja": word_entry["ja"] if word_entry else "",
                "translation_de": word_entry["de"] if word_entry else "",
                "translation_fr": word_entry["fr"] if word_entry else "",
                "translation_la": word_entry["la"] if word_entry else "",
            }

            return PluginResult(available=True, data=data)
        except Exception as e:
            logger.exception("Error fetching word of the day")
            return PluginResult(available=False, error=str(e))

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []

    def cleanup(self) -> None:
        pass


Plugin = WordOfDayPlugin

"""Display a word, its pronunciation, and definition from the Free Dictionary API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List
import requests

from src.plugins.base import PluginBase, PluginResult

logger = logging.getLogger(__name__)

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
USER_AGENT = "FiestaBoard Word of the Day Plugin (https://github.com/Fiestaboard/fiestaboard-plugin--word-of-day)"


class WordOfDayPlugin(PluginBase):
    """Word of the Day plugin for FiestaBoard."""

    @property
    def plugin_id(self) -> str:
        return "word_of_day"

    def fetch_data(self) -> PluginResult:
        import datetime

        # Curated word list — one word cycles per day
        WORD_LIST = [
            "ephemeral", "serendipity", "luminous", "quixotic", "mellifluous",
            "perspicacious", "ebullient", "surreptitious", "idyllic", "veracious",
            "eloquent", "fortuitous", "ineffable", "penultimate", "sanguine",
            "vivacious", "tenacious", "ubiquitous", "paradox", "nostalgia",
            "ethereal", "magnanimous", "loquacious", "resilient", "altruistic",
            "benevolent", "candid", "diligent", "erudite", "fervent",
            "gregarious", "humble", "inquisitive", "jovial", "kinetic",
        ]

        try:
            custom_word = (self.config.get("custom_word") or "").strip().lower()
            if custom_word:
                word = custom_word
            else:
                day_of_year = datetime.date.today().timetuple().tm_yday
                word = WORD_LIST[day_of_year % len(WORD_LIST)]

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
                    definition = str(defs[0].get("definition", ""))[:22]

            return PluginResult(
                available=True,
                data={
                    "word": word,
                    "part_of_speech": part_of_speech,
                    "definition": definition,
                    "phonetic": phonetic,
                },
            )
        except Exception as e:
            logger.exception("Error fetching word of the day")
            return PluginResult(available=False, error=str(e))

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        return []

    def cleanup(self) -> None:
        pass

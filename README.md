# Word of the Day Plugin

Display a word, its pronunciation, and definition from the Free Dictionary API.

![Word of the Day Display](./docs/board-display.png)

**→ [Setup Guide](./docs/SETUP.md)**

## Overview

The Word of the Day plugin fetches a word definition from dictionaryapi.dev. Because the API doesn't offer a daily-word endpoint, the plugin selects a word based on a curated list, cycling one per day. No API key required.

## Template Variables

| Variable | Description | Example |
|---|---|---|
| `word_of_day.word` | The word | `ephemeral` |
| `word_of_day.part_of_speech` | Part of speech (noun, verb, etc.) | `adjective` |
| `word_of_day.definition` | Short definition | `lasting a short time` |
| `word_of_day.phonetic` | Phonetic spelling | `/ɪˈfem(ə)r(ə)l/` |

## Example Templates

```
WORD OF THE DAY
{{word_of_day.word}}
{{word_of_day.phonetic}}
{{word_of_day.part_of_speech}}
{{word_of_day.definition}}

```

## Configuration

| Setting | Name | Description | Required |
|---|---|---|---|
| `custom_word` | Custom Word | Leave blank to show a daily word from the built-in list, or enter a word to always show. | No |

## Features

- Free Dictionary API (no API key)
- Daily word rotation from curated list
- Custom word override
- Part of speech and phonetic

## Author

FiestaBoard Team

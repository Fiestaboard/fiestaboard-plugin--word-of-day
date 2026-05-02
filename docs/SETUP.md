# Word of the Day Setup Guide

Display a word, its pronunciation, and definition from the Free Dictionary API.

## Overview

The Word of the Day plugin fetches a word definition from dictionaryapi.dev. Because the API doesn't offer a daily-word endpoint, the plugin selects a word based on a curated list, cycling one per day. No API key required.

- API reference: https://dictionaryapi.dev/

### Prerequisites

No API key required.

## Quick Setup

1. **Enable** — Go to **Integrations** in your FiestaBoard settings and enable **Word of the Day**.
2. **Configure** — Fill in the plugin settings (see Configuration Reference below).
3. **Template** — Add a page using the `word_of_day` plugin variables:
   ```
   {{{ word_of_day.status }}}
   ```
4. **View** — Navigate to your board page to see the live display.

## Template Variables

| Variable | Description | Example |
|---|---|---|
| `word_of_day.word` | The word | `ephemeral` |
| `word_of_day.part_of_speech` | Part of speech (noun, verb, etc.) | `adjective` |
| `word_of_day.definition` | Short definition | `lasting a short time` |
| `word_of_day.phonetic` | Phonetic spelling | `/ɪˈfem(ə)r(ə)l/` |

## Configuration Reference

| Setting | Name | Description | Default |
|---|---|---|---|
| `enabled` | Enabled |  | `False` |
| `custom_word` | Custom Word | Leave blank to show a daily word from the built-in list, or enter a word to always show. | `` |
| `refresh_seconds` | Refresh Interval (seconds) | How often to refresh (once per day is sufficient). | `3600` |

## Troubleshooting

- **Word not found** — the Free Dictionary API doesn't cover all words. Try a common word.
- **Always same word** — check if `custom_word` is set. Clear it for daily rotation.


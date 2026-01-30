# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Issue Tracking

**This repository is managed with Beads** - a git-native issue tracker. When working here:
- Use the `using-beads` skill when discovering work, updating progress, or managing dependencies
- Create issues with `bd create` when you find new work
- Update status with `bd update <id> --status <status>` as you progress
- Use `bd ready` to find unblocked work ready to claim
- Close issues with `bd close <id>` when complete and customer is satisfied

Run `bd quickstart` for quick reference, or use the skill for detailed guidance.

## Project Overview

**Spotify DJ** - A conversational CLI application that uses an LLM (via OpenRouter) to interpret natural language requests and manage a Spotify queue. Users describe their mood or music preferences, and the LLM translates this into queue modifications.

## Architecture

The system has three main components that work in a loop:

1. **CLI Loop** (`main.py`) - Reads user input, maintains conversation history across the session
2. **LLM Client** (`llm_client.py`) - Sends context to OpenRouter API:
   - User message
   - Current queue state (fetched from Spotify)
   - Full conversation history
   - Returns desired queue as JSON: `{"queue": [{"title": "...", "artist": "..."}]}`
3. **Spotify Sync Engine** (`queue_sync.py` + `spotify_client.py`) - Reconciles desired queue with actual Spotify state:
   - Converts title/artist pairs to Spotify IDs via search
   - Clears current queue
   - Adds songs in order

**Key Design Decision**: The LLM doesn't call tools directly. Instead, it outputs a structured queue plan, and the sync engine handles all Spotify API operations. This avoids hallucinated tool calls and separates creative (what to play) from mechanical (how to modify Spotify).

## Development Commands

**Python Environment**: This project uses `uv` with a virtual environment at `.venv/`

Always use `.venv/bin/python` and `.venv/bin/pip` for all Python commands.

**Testing Components**:
```bash
# Test Spotify client and queue fetching
.venv/bin/python test_spotify_client.py

# Run the main CLI application
.venv/bin/python main.py
```

**Environment Setup**:
- Copy `.env.example` to `.env` and fill in credentials:
  - `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI` (Spotify OAuth)
  - `OPENROUTER_API_KEY` (LLM API access)

## Implementation Status

**Completed**:
- Task 1: Project setup (requirements.txt, .env.example, main.py stub)
- Task 2: Spotify authentication & queue fetching (spotify_client.py with `get_current_queue()`)

**Remaining** (see `docs/plans/2026-01-16-spotify-dj-implementation.md`):
- Task 3: LLM API Client (OpenRouter integration)
- Task 4: Queue Sync Engine (title/artist → Spotify ID, queue modification)
- Task 5: Conversation History Management
- Task 6: CLI Loop & Main Application
- Task 7: Polish & Edge Cases

## Key Technical Details

**Spotify Queue Structure**: `get_current_queue()` returns a list where:
- First item: currently playing track
- Remaining items: queued tracks in order

**LLM Queue Format**: The LLM receives and returns queues as:
```json
{"queue": [{"title": "Song Name", "artist": "Artist Name"}, ...]}
```

**Spotify Scopes Required**: `user-read-playback-state,user-modify-playback-state`

**Song Lookup Strategy**: Use Spotipy's search with query format: `"{title} {artist}"` to find Spotify track IDs. Handle lookup failures gracefully (skip song, log warning).

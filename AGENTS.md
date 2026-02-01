# AGENTS.md

This file provides guidance to agents when working with code in this repository.

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
2. **LLM Client** (`src/spotify_dj/llm_client.py`) - Sends context to OpenRouter API:
   - User message
   - Current queue state (fetched from Spotify)
   - Full conversation history
   - Returns desired queue as JSON: `{"queue": [{"title": "...", "artist": "..."}]}`
3. **Spotify Sync Engine** (`src/spotify_dj/queue_sync.py` + `src/spotify_dj/spotify_client.py`) - Reconciles desired queue with actual Spotify state:
   - Converts title/artist pairs to Spotify IDs via search
   - Clears current queue
   - Adds songs in order

**Package Structure**:
- `src/spotify_dj/` - Main package containing all modules
- `main.py` - CLI entry point (root level)
- `test_*.py` - Test scripts (root level)
- `pyproject.toml` - Package configuration (hatchling build backend)

**Key Design Decision**: The LLM doesn't call tools directly. Instead, it outputs a structured queue plan, and the sync engine handles all Spotify API operations. This avoids hallucinated tool calls and separates creative (what to play) from mechanical (how to modify Spotify).

## Development Commands

**Python Environment**: This project uses `uv` with a virtual environment at `.venv/`

**Setup**:
```bash
# Create virtual environment (if not exists)
uv venv

# Install package in editable mode
uv pip install -e .

# For development with linting and testing tools
uv pip install -e ".[dev]"
```

**Testing Components**:
```bash
# Test Spotify client and queue fetching
uv run python test_spotify_client.py

# Run the main CLI application
uv run python main.py

# Run all tests
uv run pytest

# Run with debug mode
uv run python main.py --debug

# Monitor debug logs
uv run python monitor.py --latest
```

**Linting & Formatting** (if dev deps installed):
```bash
# Format code with black
black src/ main.py test_*.py

# Lint with ruff
ruff check src/ main.py test_*.py

# Type check with mypy
mypy src/
```

**Environment Setup**:
- Copy `.env.example` to `.env` and fill in credentials:
  - `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `SPOTIFY_REDIRECT_URI` (Spotify OAuth)
  - `OPENROUTER_API_KEY` (LLM API access)

## Implementation Status

**Completed**:
- Task 1: Project setup (pyproject.toml, .env.example, main.py stub)
- Task 2: Package structure with src/ layout (src/spotify_dj/)
- Task 3: Spotify authentication & queue fetching (src/spotify_dj/spotify_client.py with `get_current_queue()`)
- Task 4: LLM API Client (OpenRouter integration)
- Task 5: Queue Sync Engine (title/artist → Spotify ID, JIT queue injection)
- Task 6: Conversation History Management
- Task 7: CLI Loop & Main Application
- Task 8: Debug logging and monitoring

**Remaining** (see `docs/plans/2026-01-16-spotify-dj-implementation.md`):
- Task 9: Polish & Edge Cases

## Key Technical Details

**Package Imports**:
- Package modules use relative imports: `from .spotify_client import ...`
- External files (main.py, test_*.py) use package imports: `from spotify_dj.spotify_client import ...`

**Spotify Queue Structure**: `get_current_queue()` returns a list where:
- First item: currently playing track
- Remaining items: queued tracks in order

**LLM Queue Format**: The LLM receives and returns queues as:
```json
{"queue": [{"title": "Song Name", "artist": "Artist Name"}, ...]}
```

**Spotify Scopes Required**: `user-read-playback-state,user-modify-playback-state`

**Song Lookup Strategy**: Use Spotipy's search with query format: `"{title} {artist}"` to find Spotify track IDs. Handle lookup failures gracefully (skip song, log warning).

**Build System**: Uses hatchling (PEP 517) with pyproject.toml configuration

# Spotify DJ

Conversational CLI that uses an LLM (via OpenRouter) to turn natural-language music requests into a structured queue plan, then keeps Spotify playback going via a Just-In-Time (JIT) queue injection loop.

Key files:
- `main.py`: interactive CLI
- `llm_client.py`: OpenRouter client that returns JSON queue suggestions
- `spotify_client.py`: Spotipy wrapper (OAuth, queue/playback primitives)
- `queue_sync.py`: JIT injection engine (background thread)
- `monitor.py`: optional Rich dashboard for debug logs

## How It Works

1. `main.py` reads user input.
2. Fetches current Spotify queue state.
3. Sends context (conversation history + queue + request) to OpenRouter.
4. OpenRouter returns JSON in the shape: `{"queue": [{"title": "...", "artist": "..."}, ...]}`.
5. The JIT engine maintains a local "shadow queue" and injects the next track into Spotify shortly before the current track ends.

Why JIT: the Spotify Web API can add to queue, but does not support removing items from the queue. Injecting one-at-a-time keeps the session steerable when the user changes their mind mid-playback.

## Setup

Python:
- Tested with Python 3.12 (other versions not confirmed).

Create a virtual environment at `.venv/` (this repo commonly uses `.venv/bin/python` and `.venv/bin/pip`):

```bash
python3 -m venv .venv
```

Install dependencies:

```bash
.venv/bin/pip install -r requirements.txt
```

Create your `.env`:

```bash
cp .env.example .env
```

Fill in `.env` (see `.env.example`):

```bash
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
OPENROUTER_API_KEY=...
```

Spotify OAuth:
- `spotify_client.py` uses `spotipy.SpotifyOAuth` with scopes `user-read-playback-state,user-modify-playback-state`.
- On first run you may be prompted to authenticate in a browser using your configured `SPOTIFY_REDIRECT_URI`.

## Run

Start the CLI:

```bash
.venv/bin/python main.py
```

Exit keywords: `exit`, `quit`, `bye`, `stop`.

### Debug Mode

Enable debug logging:

```bash
.venv/bin/python main.py --debug
```

This writes session logs to `logs/session_<timestamp>_<pid>.jsonl`.

### Monitor Dashboard

Watch the latest debug session:

```bash
.venv/bin/python monitor.py --latest
```

Or watch a specific log file:

```bash
.venv/bin/python monitor.py --file logs/session_<timestamp>_<pid>.jsonl
```

## Tests

These are runnable as standalone scripts:

```bash
.venv/bin/python test_conversation.py
.venv/bin/python test_llm_extraction.py
.venv/bin/python test_llm_client.py
.venv/bin/python test_spotify_client.py
.venv/bin/python test_queue_sync.py
.venv/bin/python test_jit_queue.py
```

Notes:
- `test_llm_client.py` requires `OPENROUTER_API_KEY`.
- Spotify-related tests require Spotify credentials and typically an active playback device.

## Troubleshooting

- Missing credentials: create `.env` from `.env.example` and fill all variables.
- Spotify device errors: start playback on a device/account first, then rerun.
- Redirect URI mismatch: ensure `SPOTIFY_REDIRECT_URI` matches what you configured in your Spotify Developer app.

## Repo Notes

- `docs/repository-structure.md` and `AGENTS.md` document the codebase layout and expected dev commands.
- This repo is managed with Beads (see `AGENTS.md`).

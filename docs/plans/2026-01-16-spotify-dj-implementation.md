# Spotify DJ Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a conversational CLI DJ powered by an LLM (via OpenRouter) that interprets user requests and manages a Spotify queue through structured JSON output.

**Architecture:**
The system has three main components: (1) a CLI loop that reads user input and maintains conversation history, (2) an LLM client that sends context (user message + current queue + history) to OpenRouter and receives a desired queue state as JSON, and (3) a Spotify sync engine using Spotipy that reconciles the desired queue with actual Spotify state. On each turn, fetch the current queue, send it with context to the LLM, parse the response, and sync the queue in Spotify.

**Tech Stack:** Python 3.10+, Spotipy, OpenRouter API, requests library

---

## Implementation Status

**Completed:**
- Task 1: Project setup (requirements.txt, .env.example, main.py stub)
- Task 2: Spotify authentication & queue fetching (spotify_client.py with `get_current_queue()`)
- Task 3: LLM API Client (OpenRouter integration)
  - Created `llm_client.py` with LLMClient class
  - Created `config.py` for centralized configuration management
  - **Current model:** `x-ai/grok-code-fast-1` (configurable in config.py line 16)
  - Implemented JSON extraction and validation with robust error handling
  - System prompt refined for strict JSON-only output format

**Remaining:**
- Task 4: Queue Sync Engine (title/artist → Spotify ID, queue modification)
- Task 5: Conversation History Management
- Task 6: CLI Loop & Main Application
- Task 7: Polish & Edge Cases

---

### Task 1: Project Setup & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `main.py` (entry point stub)

**Step 1: Create requirements.txt with core dependencies**

List all needed packages: spotipy, requests, python-dotenv, and any others for CLI/JSON handling.

**Step 2: Create .env.example**

Template showing required environment variables: SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_USER, OPENROUTER_API_KEY

**Step 3: Create main.py stub**

Bare minimum entry point that imports and runs the CLI loop (doesn't exist yet, will be built in later tasks).

**Step 4: Commit**

Commit these setup files with message "setup: initialize project structure"

---

### Task 2: Spotify Authentication & Queue Fetching

**Files:**
- Create: `spotify_client.py`
- Create: `.env` (user fills in their credentials)

**Step 1: Write SpotifyClient class stub**

Create a class that initializes Spotipy with credentials from environment variables. Include a method `get_current_queue()` that returns queue as list of dicts with `title` and `artist`.

**Step 2: Implement get_current_queue()**

Use Spotipy to fetch the current user's queue. Parse the response to extract song title and artist for each track. Return as list of dicts: `[{"title": "...", "artist": "..."}, ...]`

**Step 3: Test manually**

Create a simple test script that initializes SpotifyClient, calls get_current_queue(), and prints the result. Verify it works with your Spotify account.

**Step 4: Commit**

Commit spotify_client.py with message "feat: add spotify queue fetching"

---

### Task 3: LLM API Client (OpenRouter)

**Files:**
- Create: `llm_client.py`

**Step 1: Write LLMClient class**

Create a class that takes an OpenRouter API key. Include a method `get_queue_suggestion(conversation_history, current_queue, user_message)` that:
- Formats the system prompt (DJ curator instructions)
- Builds the full prompt with conversation history, current queue JSON, and new user message
- Sends to OpenRouter API
- Returns the response

**Step 2: Implement the system prompt**

Write a prompt that instructs the LLM to be a DJ curator. Tell it to receive the current queue and user requests, and output the new desired queue as JSON in the format: `{"queue": [{"title": "...", "artist": "..."}]}`

**Step 3: Call OpenRouter API**

Use requests to POST to OpenRouter with the formatted prompt. Handle the API response and extract the LLM's text output.

**Step 4: Parse JSON response**

Extract the queue JSON from the LLM's response. Validate it has the correct structure. Return the parsed queue.

**Step 5: Test manually**

Create a test script that initializes LLMClient, sends a test message (like "add upbeat indie"), and prints the returned queue structure. Verify the JSON is valid.

**Step 6: Commit**

Commit llm_client.py with message "feat: add openrouter llm client"

---

### Task 4: Queue Sync Engine (PARTIALLY COMPLETE - JIT REQUIRED)

**Status:** Basic implementation done, but blocked by Spotify API limitation.

**Blocker:** Spotify Web API does NOT support removing songs from queue. Only read and add operations available.

**Solution:** See Task 4.5 - Just-in-Time Queue Injection (REQUIRED BEFORE TASK 6)

---

### Task 4.5: Just-in-Time Queue Injection System

**CRITICAL:** This task must be completed and tested before moving to Task 6.

**Overview:** Instead of trying to "clear" the Spotify queue, maintain a "Shadow Queue" in Python. The script monitors playback and injects the next song 10-20 seconds before the current song ends. This solves the API limitation elegantly.

**How it works:**
1. Python maintains a shadow queue list (from LLM suggestions)
2. Start playback with first song via `start_playback()`
3. Run polling loop checking `currently_playing()` every 1-2 seconds
4. When current song is within 10-20 seconds of ending, inject next song via `add_to_queue()`
5. If user changes request, update shadow queue immediately
6. User manual interference (skipping, adding songs) is fine - script only controls injected songs

**Files:**
- Modify: `spotify_client.py` (add JIT methods)
- Rewrite: `queue_sync.py` (JIT-based queue controller)
- Create: `queue_manager.py` (shadow queue management)
- Create: `test_jit_queue.py` (comprehensive testing)
- Modify: `config.py` (add JIT timing config)

**Step 1: Add JIT configuration to config.py**

Add a new `JITConfig` class:
```python
class JITConfig:
    INJECTION_THRESHOLD = 15  # Seconds before song ends to inject next
    POLL_INTERVAL = 1.5       # Seconds between playback checks
    MIN_QUEUE_SIZE = 1        # Minimum songs in Spotify queue
```

**Step 2: Enhance SpotifyClient with JIT methods**

Add methods to spotify_client.py:
- `start_playback(track_uri)` - Start playing specific track
- `get_playback_status()` - Get progress_ms, duration_ms, is_playing
- `calculate_time_until_end()` - Returns seconds until current song ends
- `should_inject_next()` - Returns True if within injection threshold
- `inject_next_song(track_uri)` - Add song to queue (remove clear_queue dependency)

**Step 3: Create QueueManager class**

Create queue_manager.py:
```python
class QueueManager:
    def __init__(self, songs_list)
    def update_queue(new_songs_list)  # Update shadow queue on the fly
    def get_next_song()               # Pop next song
    def peek_next_song()              # Look at next without removing
    def is_empty()
    def queue_length()
```

**Step 4: Rewrite QueueSync for JIT**

Rewrite queue_sync.py:
```python
class JITQueueSync:
    def start_dj_session(initial_queue)     # Begin with first song
    def run_injection_loop()                # Main polling/injection loop
    def update_shadow_queue(new_queue)      # Update queue mid-session
    def stop_session()                      # Stop loop cleanly
```

The injection loop:
- Polls playback status every POLL_INTERVAL seconds
- Checks if should_inject_next() returns True
- Gets next song from QueueManager and injects it
- Continues until shadow queue empty or stopped
- Handles paused/stopped playback gracefully

**Step 5: Handle edge cases**

- Song ends before injection trigger: Get next and inject immediately
- Playback paused: Don't inject, wait for resume
- No playback: Initialize with first song
- Shadow queue empty: Stop and inform user
- Network errors: Retry with backoff
- Multiple queue updates: Process them in order

**Step 6: Test JIT thoroughly**

Create test_jit_queue.py:
- Set up 10+ song queue
- Start playback
- Run injection loop for 30+ seconds
- Verify injections happen at correct times
- Update shadow queue mid-playback, verify next injection uses new songs
- Test edge cases: pause, skip, network simulation

**Step 7: Commit**

Commit with message "feat: implement just-in-time queue injection system"

---

### Task 5: Conversation History Management

**Files:**
- Create: `conversation.py`

**Step 1: Write ConversationHistory class**

Create a class that stores and manages conversation messages. Include methods:
- `add_user_message(text)` - adds a user message
- `add_assistant_response(text)` - adds LLM response
- `get_history()` - returns full conversation in format suitable for LLM (list of dicts with role and content)
- `clear()` - resets history

**Step 2: Format history for LLM**

The `get_history()` method should return something like: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]` in chronological order.

**Step 3: Test manually**

Create a test that adds a few messages and verifies get_history() returns the correct format.

**Step 4: Commit**

Commit conversation.py with message "feat: add conversation history management"

---

### Task 6: CLI Loop & Main Application

**Files:**
- Modify: `main.py`
- Create: `cli.py` (optional, if you want to separate CLI logic)

**Step 1: Write the main CLI loop**

In main.py, create a function that:
- Initializes SpotifyClient, LLMClient, QueueSync, and ConversationHistory
- Enters an infinite loop that:
  - Prompts user for input
  - Fetches current queue from Spotify
  - Calls LLMClient with conversation history + current queue + user message
  - Parses the returned queue structure
  - Calls QueueSync to update Spotify
  - Stores user message and LLM response in ConversationHistory
  - Loops until user exits (e.g., types "exit")

**Step 2: Add user exit handling**

Allow user to type "exit" or "quit" to end the session gracefully.

**Step 3: Add error handling**

Wrap main loop in try/except to handle API errors, JSON parsing errors, etc. Print user-friendly error messages.

**Step 4: Test end-to-end**

Run the CLI, send a few requests, verify the queue updates in Spotify in real-time.

**Step 5: Commit**

Commit main.py with message "feat: add cli loop and main application"

---

### Task 7: Polish & Edge Cases

**Files:**
- Modify: Files as needed for robustness

**Step 1: Handle empty queue responses**

If LLM returns an empty queue, allow it (user might say "clear everything").

**Step 2: Handle song lookup failures**

If a song can't be found on Spotify, log a warning and skip it instead of crashing.

**Step 3: Add user feedback**

Print what the program is doing: "Fetching queue...", "Calling LLM...", "Syncing to Spotify...", etc.

**Step 4: Test edge cases**

- User requests to clear queue
- LLM suggests non-existent songs
- Network errors during API calls
- Malformed LLM responses

**Step 5: Commit**

Commit with message "feat: add error handling and user feedback"

---

# Spotify DJ Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a conversational CLI DJ powered by an LLM (via OpenRouter) that interprets user requests and manages a Spotify queue through structured JSON output.

**Architecture:**
The system has three main components: (1) a CLI loop that reads user input and maintains conversation history, (2) an LLM client that sends context (user message + current queue + history) to OpenRouter and receives a desired queue state as JSON, and (3) a Spotify sync engine using Spotipy that reconciles the desired queue with actual Spotify state. On each turn, fetch the current queue, send it with context to the LLM, parse the response, and sync the queue in Spotify.

**Tech Stack:** Python 3.10+, Spotipy, OpenRouter API, requests library

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

### Task 4: Queue Sync Engine

**Files:**
- Create: `queue_sync.py`
- Modify: `spotify_client.py` (add queue modification methods)

**Step 1: Add queue modification methods to SpotifyClient**

Add methods: `clear_queue()`, `add_songs_to_queue(songs_list)` where songs_list is `[{"title": "...", "artist": "..."}]`. The add method should convert title/artist to Spotify IDs using Spotipy's search, then add them to the queue.

**Step 2: Write QueueSync class**

Create a class that takes a SpotifyClient instance. Include a method `sync_queue(desired_queue)` that:
- Takes the desired queue from LLM (list of dicts with title/artist)
- Clears the current Spotify queue
- Adds songs from desired_queue in order

**Step 3: Implement title/artist to Spotify ID lookup**

Use Spotipy's search feature to find tracks by title and artist. Handle cases where exact matches aren't found (log a warning, skip that song).

**Step 4: Test sync manually**

Create a test script that calls sync_queue with a sample desired queue. Verify songs are added to your Spotify queue in the correct order.

**Step 5: Commit**

Commit queue_sync.py and spotify_client.py changes with message "feat: add queue sync engine"

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

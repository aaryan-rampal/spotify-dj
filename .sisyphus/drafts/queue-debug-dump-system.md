# Draft: Queue Debug State Dump System

## User Requirements (REVISED)

**Goal:** Real-time visual debugging of queue state while Spotify DJ runs

**Key Insight from User:**
- "want a debugger when i run this" → REAL-TIME visibility, not static files
- "maybe a website or some sort of gui" → Visual interface preferred
- "but i want it to be easy asf" → Minimal setup, no complexity
- "main point will be at some point maybe a website" → Web UI is future goal
- "mvp is cli, so i dont want to go crazy" → Keep simple for now

**Core Need:** Easy-to-use real-time visualizer for queue state, injection events, and Spotify sync

---

## Agent Research Findings

### 1. Existing Logging Patterns (Agent: bg_8084b2a6)

**Current State:**
- 251 print() statements across 11 files
- 0 instances of Python's logging module
- 70 try/except patterns across 8 files
- No structured output levels (INFO, WARNING, ERROR, DEBUG)
- No automatic timestamps
- No log rotation or file-based logging
- Thread safety concern: background injection thread prints to stdout

**Print Statement Locations:**
- `queue_sync.py`: 20 prints (session lifecycle, injection tracking, errors)
- `spotify_client.py`: 9 prints (search errors, playback errors, queue ops)
- `queue_manager.py`: 4 prints (validation warnings)
- `llm_client.py`: 4 DEBUG prints (API troubleshooting)
- `main.py`: 35+ prints (CLI user interface feedback)

---

### 2. Injection Loop Analysis (Agent: bg_651a474a)

**State Variables Tracked:**
```python
# JITQueueSync instance variables
self.client                # SpotifyClient instance
self.queue_manager         # QueueManager instance (shadow queue)
self.running              # Loop control flag
self.injection_thread      # Thread reference
self.last_injected_uri     # Last URI successfully injected
self.last_played_uri      # Currently playing song URI
self.already_injected_for_current  # One injection per song flag

# Local variables in run_injection_loop()
start_time              # Session start timestamp
elapsed                 # Time elapsed
status                  # Playback status dict
current_playback         # Spotify API response
current_uri             # URI of currently playing track
next_uri                # Next song URI to inject
injected                # Injection success flag
time_left               # Seconds until track ends
attempt                 # Retry counter
```

**External Calls Each Poll Cycle:**
1. `self.client.get_playback_status()` - Line 112
2. `self.client.sp.current_playback()` - Line 118 (REDUNDANT!)
3. `self.client.calculate_time_until_end()` - Line 145
4. `self.client.inject_next_song(next_uri)` - Line 146
5. `self.queue_manager.is_empty()` - Line 133
6. `self.queue_manager.get_next_track_uri()` - Line 137
7. `self.queue_manager.get_next_song()` - Line 148

**Critical Issues Found:**
- **Redundant API call**: Lines 112 and 118 both call `current_playback()` - should consolidate
- **Silent failures**: Failed injections (line 160) continue without tracking which songs failed
- **No metrics**: No success/failure rates, timing data, or session statistics
- **Race conditions**: Device switches mid-song, playback state changes between checks
- **Same song edge case**: Won't detect "change" if same song plays twice

**Information NOT Currently Captured:**

Per-Cycle:
- Poll/iteration number
- Timestamp of each poll
- playback.progress_ms, duration_ms
- Shadow queue length
- State of all flags (already_injected_for_current, etc.)

Injection Events:
- Song details being injected (title, artist, URI)
- Retry attempt numbers
- Time remaining when triggered
- Success/failure status with error messages

Session Metrics:
- Total poll cycles
- Successful vs failed injections
- Song change detection events
- Total runtime

Error Context:
- Spotify API error messages
- Exception types and stack traces
- Network timeout details

---

## Proposed Design

### Queue State Dump Output Format

```
=== Queue State Dump ===
Timestamp: 2026-01-29 19:45:23.456
Cycle: 1
Time in Session: 12.3s

[PLAYING]
Title: Song Name
Artist: Artist Name
URI: spotify:track:...
Progress: 2m15s / 3m45s (60.0%)
Time Until End: 90s
Device: My MacBook Pro

[SHADOW QUEUE]
Remaining: 15 songs
Current Index: 3 (3 songs injected so far)
Next to Inject: Next Song by Next Artist
URI: spotify:track:...

[SPOTIFY QUEUE]
Items: 1 (currently playing) + 2 in queue
Queue:
  1. Song Name by Artist Name [PLAYING]
  2. Next Song by Next Artist [QUEUED]
  3. Another Song by Another Artist [QUEUED]

[INJECTION STATE]
Should Inject: NO (90s > 15s threshold)
Last Injected URI: spotify:track:...
Already Injected for Current: YES
Injection Flag State: False

[EVENTS]
None this cycle
```

### Activation

```python
# main.py
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--debug", action="store_true", help="Enable queue state dumping")
args = parser.parse_args()

if args.debug:
    # Enable queue state dump system
```

### Implementation Approach

**Option 1: Create dedicated QueueDumper class**
- Independent of existing logging
- Writes to logs/queue_dump_{timestamp}.txt
- Called from injection loop every poll cycle
- Can be enabled/disabled cleanly

**Option 2: Enhance JITQueueSync with built-in dumping**
- Add `enable_debug_dump` parameter
- Integrate dump calls into run_injection_loop()
- Cleaner but more invasive to existing code

---

## Design Decisions (CONFIRMED)

**Visualization Approach:** CLI Dashboard (rich library)
- Terminal-based real-time visualizer
- `pip install rich` (simple setup)
- Runs in same terminal as CLI
- Can evolve to web UI later (textual has web mode)

**Dashboard Content:** Comprehensive - all data
- Queue state (playing song, shadow queue, injection status)
- LLM suggestions (what queue was requested)
- User requests (what triggered updates)
- Spotify API errors (detailed error messages)
- Retry attempts and timing metrics
- Session statistics (success/failure rates, total runtime)

**Activation:** `--debug` flag (as originally requested)

---

## Key Design Choice (OPEN)

The current CLI uses `input()` in `main.py` while the JIT injection loop runs in a background thread.
If we try to render a live-updating `rich` dashboard in the same terminal at the same time as `input()`, output can get messy (cursor jumps, partial prompts, mixed lines).

**Recommended MVP (easy + reliable):**
- `--debug` writes rich, readable snapshots/events to a single session log file in `logs/`
- a separate "monitor" mode renders a `rich` dashboard by tailing that log file (run in another terminal pane)

This keeps the main CLI interaction stable while still giving you a real-time dashboard.

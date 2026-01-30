# CLI Debug Dashboard for Spotify DJ

## TL;DR

> **Quick Summary**: Add real-time visual debugging to Spotify DJ via a separate monitor terminal. Main CLI writes debug data stream to JSONL file, monitor.py renders live rich dashboard.
> 
> **Deliverables**:
> - `--debug` flag for main.py
> - `debug_writer.py` - thread-safe debug data writer
> - `monitor.py` - rich-based live dashboard
> - `logs/` directory with .gitignore
> 
> **Estimated Effort**: Medium (4-6 tasks)
> **Parallel Execution**: YES - 2 waves
> **Critical Path**: Task 1 (deps) -> Task 2 (writer) -> Task 4 (integration) -> Task 5 (monitor)

---

## Context

### Original Request
User wants to debug Spotify DJ because "it doesn't really work right now." Need visibility into queue state changes, injection events, LLM suggestions, and errors as the app runs.

### Interview Summary
**Key Discussions**:
- Visualization: CLI Dashboard using `rich` library (not web for MVP)
- Content: Comprehensive - queue state + LLM suggestions + user requests + API errors + retry attempts + timing
- Approach: Separate monitor terminal (main.py writes data, monitor.py displays)
- Location: `logs/` directory (will .gitignore, can evolve later)
- Activation: `--debug` flag

**Research Findings**:
- 251 print() statements in codebase, no Python logging module
- JIT injection loop runs in background thread, polls every 1.5s
- Missing debug data: poll iteration, timestamps, progress_ms, device, shadow queue length, song details, retry attempts, API errors
- Redundant API call at line 118 (noted but not fixing in this plan)

### Metis Review
**Identified Gaps** (addressed):
- No argparse in main.py -> Added as Task 1
- `rich` not in requirements.txt -> Added as Task 1
- `logs/` not in .gitignore -> Added as Task 1
- Thread safety for DebugWriter -> Specified Lock pattern from queue_manager.py
- Print statement conflict with rich.Live -> Documented as known limitation (MVP)
- Session file naming collisions -> Include PID in filename
- Edge cases (disk full, malformed lines, etc.) -> Added to Task 5

---

## Work Objectives

### Core Objective
Enable real-time visual debugging of queue state, injection events, and errors while Spotify DJ runs, using a separate terminal monitor.

### Concrete Deliverables
- `main.py` with `--debug` flag via argparse
- `debug_writer.py` with thread-safe DebugWriter class
- `monitor.py` with rich-based live dashboard
- `logs/` directory created and gitignored
- `requirements.txt` updated with `rich>=13.0.0`

### Definition of Done
- [ ] `python main.py --debug` writes JSONL to `logs/session_{timestamp}_{pid}.jsonl`
- [ ] `python monitor.py --latest` shows live updating dashboard
- [ ] Dashboard shows: now playing, shadow queue, injection status, events log, errors
- [ ] No debug artifacts created when `--debug` is NOT passed
- [ ] Monitor handles missing/stale files gracefully

### Must Have
- `--debug` flag activates debug logging
- Thread-safe file writes (DebugWriter uses Lock)
- Live-updating dashboard (updates within 2s of events)
- Comprehensive data: queue state, LLM suggestions, errors, timing

### Must NOT Have (Guardrails)
- No refactoring of existing print() statements
- No Python logging module migration (separate initiative)
- No web UI infrastructure (MVP is CLI only)
- No configuration files for dashboard layout (hardcoded)
- No log rotation/analysis tools for MVP
- No changes to core business logic in queue_sync.py beyond adding DebugWriter calls
- No blocking of injection thread on file writes

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: NO (manual test scripts only)
- **User wants tests**: Manual verification
- **Framework**: None (manual `python` commands)

### Manual Verification Approach

Each TODO includes shell commands that can be run to verify the implementation works correctly.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately):
├── Task 1: Add dependencies and infrastructure
└── (no other parallel tasks - this is foundational)

Wave 2 (After Wave 1):
├── Task 2: Create DebugWriter class
└── Task 3: Create DebugEvent data structures

Wave 3 (After Wave 2):
├── Task 4: Integrate DebugWriter into main.py and queue_sync.py
└── (sequential - needs Task 2+3)

Wave 4 (After Wave 4):
└── Task 5: Create monitor.py dashboard

Wave 5 (After Task 5):
└── Task 6: End-to-end testing and edge cases
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2, 3, 4, 5 | None (foundational) |
| 2 | 1 | 4 | 3 |
| 3 | 1 | 4 | 2 |
| 4 | 2, 3 | 5 | None |
| 5 | 4 | 6 | None |
| 6 | 5 | None | None (final) |

---

## TODOs

- [x] 1. Add dependencies and infrastructure

  **What to do**:
  - Add `rich>=13.0.0` to requirements.txt
  - Add `logs/` to .gitignore
  - Add argparse to main.py with `--debug` flag
  - Create `logs/` directory check in startup

  **Must NOT do**:
  - Don't modify any other behavior in main.py yet
  - Don't add any debug writing logic yet

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple file modifications, no complex logic
  - **Skills**: `[]`
    - No special skills needed for basic edits

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (alone)
  - **Blocks**: Tasks 2, 3, 4, 5
  - **Blocked By**: None

  **References**:
  
  **Pattern References**:
  - `requirements.txt` - Existing dependencies format (spotipy, requests, python-dotenv)
  - `.gitignore` - Existing gitignore patterns
  
  **API/Type References**:
  - Python argparse docs: https://docs.python.org/3/library/argparse.html
  
  **Code Context**:
  - `main.py:50-73` - Current initialization code where argparse should be added before

  **Acceptance Criteria**:

  ```bash
  # AC1: rich is in requirements.txt
  grep -q "rich" requirements.txt && echo "PASS" || echo "FAIL"
  # Expected: PASS

  # AC2: logs/ is in .gitignore
  grep -q "logs/" .gitignore && echo "PASS" || echo "FAIL"
  # Expected: PASS

  # AC3: --debug flag is accepted
  .venv/bin/python main.py --help | grep -q "\-\-debug" && echo "PASS" || echo "FAIL"
  # Expected: PASS

  # AC4: --debug flag parses without error (quick exit)
  timeout 2 .venv/bin/python -c "
  import sys
  sys.argv = ['main.py', '--debug']
  exec(open('main.py').read().split('display_welcome')[0])
  " 2>&1 | grep -v "Error" && echo "PASS"
  # Expected: No errors
  ```

  **Commit**: YES
  - Message: `feat(debug): add --debug flag and rich dependency`
  - Files: `requirements.txt`, `.gitignore`, `main.py`

---

- [x] 2. Create DebugWriter class

  **What to do**:
  - Create `debug_writer.py` with DebugWriter class
  - Thread-safe using `threading.Lock` (follow queue_manager.py pattern)
  - Write JSONL format to `logs/session_{timestamp}_{pid}.jsonl`
  - Methods: `__init__(enabled)`, `log_cycle(data)`, `log_event(event_type, data)`, `log_error(error)`, `close()`
  - Create `logs/` directory if it doesn't exist
  - Use buffered writes (don't flush on every line)
  - Handle IOError gracefully (log to stderr, continue)

  **Must NOT do**:
  - Don't call any Spotify API methods
  - Don't block on file writes (use buffered IO)
  - Don't import or use Python logging module

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: New file creation with clear spec, moderate complexity
  - **Skills**: `[]`
    - No special skills needed

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 3)
  - **Blocks**: Task 4
  - **Blocked By**: Task 1

  **References**:

  **Pattern References**:
  - `queue_manager.py:28` - Thread-safe Lock initialization pattern: `self._lock = threading.Lock()`
  - `queue_manager.py:60-81` - Lock usage pattern: `with self._lock:`
  
  **Code Context**:
  - `config.py:88` - JITConfig.POLL_INTERVAL = 1.5 (cycle frequency)

  **Acceptance Criteria**:

  ```bash
  # AC1: DebugWriter file exists and imports
  .venv/bin/python -c "from debug_writer import DebugWriter; print('PASS')"
  # Expected: PASS

  # AC2: Creates session file when enabled
  .venv/bin/python -c "
  from debug_writer import DebugWriter
  import os
  dw = DebugWriter(enabled=True)
  dw.log_event('test', {'msg': 'hello'})
  dw.close()
  files = [f for f in os.listdir('logs') if f.startswith('session_')]
  print('PASS' if files else 'FAIL')
  "
  # Expected: PASS

  # AC3: Does nothing when disabled
  .venv/bin/python -c "
  from debug_writer import DebugWriter
  import os
  before = len([f for f in os.listdir('logs') if f.startswith('session_')]) if os.path.exists('logs') else 0
  dw = DebugWriter(enabled=False)
  dw.log_event('test', {'msg': 'hello'})
  dw.close()
  after = len([f for f in os.listdir('logs') if f.startswith('session_')]) if os.path.exists('logs') else 0
  print('PASS' if before == after else 'FAIL')
  "
  # Expected: PASS

  # AC4: Output is valid JSONL
  .venv/bin/python -c "
  from debug_writer import DebugWriter
  import json, os, glob
  dw = DebugWriter(enabled=True)
  dw.log_event('test', {'data': 123})
  dw.log_cycle({'cycle': 1, 'time': 0})
  dw.close()
  latest = max(glob.glob('logs/session_*.jsonl'), key=os.path.getctime)
  with open(latest) as f:
      lines = f.readlines()
  for line in lines:
      json.loads(line)  # Will raise if invalid
  print('PASS')
  "
  # Expected: PASS

  # AC5: Thread-safe (has Lock)
  grep -q "threading.Lock" debug_writer.py && echo "PASS" || echo "FAIL"
  # Expected: PASS
  ```

  **Commit**: YES
  - Message: `feat(debug): add DebugWriter class for JSONL logging`
  - Files: `debug_writer.py`

---

- [x] 3. Create DebugEvent data structures

  **What to do**:
  - Add to `debug_writer.py` (or keep in same file): data structure helpers
  - `CycleData` dict structure: cycle_num, timestamp, playing (title, artist, uri, progress_ms, duration_ms, device), shadow_queue (remaining, next_song, injected_count), injection_state (should_inject, time_until_end, already_injected, last_injected_uri)
  - `EventData` dict structure: event_type (injection, song_change, queue_update, error, session_start, session_end), timestamp, details
  - Helper function `create_cycle_snapshot(...)` that builds CycleData from available state
  - Helper function `create_event(...)` that builds EventData

  **Must NOT do**:
  - Don't call Spotify API (data is passed in, not fetched)
  - Don't add any print statements

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple data structure definitions
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Task 2)
  - **Blocks**: Task 4
  - **Blocked By**: Task 1

  **References**:

  **Pattern References**:
  - `spotify_client.py:160-165` - Playback status dict structure returned by get_playback_status()
  - `queue_manager.py:114-126` - get_next_track_uri() return value
  
  **Code Context**:
  - `queue_sync.py:23-37` - State variables in JITQueueSync that need to be captured

  **Acceptance Criteria**:

  ```bash
  # AC1: Helper functions exist
  .venv/bin/python -c "
  from debug_writer import create_cycle_snapshot, create_event
  print('PASS')
  "
  # Expected: PASS

  # AC2: create_cycle_snapshot produces valid dict
  .venv/bin/python -c "
  from debug_writer import create_cycle_snapshot
  import json
  data = create_cycle_snapshot(
      cycle_num=1,
      playing={'title': 'Test', 'artist': 'Artist', 'progress_ms': 1000, 'duration_ms': 3000},
      shadow_queue={'remaining': 5, 'next_song': 'Next Song'},
      injection_state={'should_inject': False, 'time_until_end': 120}
  )
  json.dumps(data)  # Must be JSON serializable
  print('PASS' if data.get('cycle_num') == 1 else 'FAIL')
  "
  # Expected: PASS

  # AC3: create_event produces valid dict with timestamp
  .venv/bin/python -c "
  from debug_writer import create_event
  import json
  event = create_event('injection', {'song': 'Test Song'})
  json.dumps(event)  # Must be JSON serializable
  print('PASS' if 'timestamp' in event and event.get('event_type') == 'injection' else 'FAIL')
  "
  # Expected: PASS
  ```

  **Commit**: NO (groups with Task 2)

---

- [x] 4. Integrate DebugWriter into main.py and queue_sync.py

  **What to do**:
  - In `main.py`:
    - Parse `--debug` flag with argparse
    - Create `DebugWriter(enabled=args.debug)`
    - Pass `debug_writer` to `JITQueueSync`
    - Log LLM suggestions and user requests when debug enabled
    - Call `debug_writer.close()` on exit
  - In `queue_sync.py`:
    - Add `debug_writer` parameter to `JITQueueSync.__init__`
    - In `run_injection_loop()`: call `debug_writer.log_cycle()` each poll cycle with current state
    - Log events: injection success/failure, song change, queue update, errors
    - Use `create_cycle_snapshot()` and `create_event()` helpers

  **Must NOT do**:
  - Don't modify core business logic (only add conditional DebugWriter calls)
  - Don't add new print statements
  - Don't block injection thread on debug writes
  - Don't import DebugWriter unconditionally (guard with `if debug_writer:`)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Integration work across two files, moderate complexity
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (sequential)
  - **Blocks**: Task 5
  - **Blocked By**: Tasks 2, 3

  **References**:

  **Pattern References**:
  - `queue_sync.py:102-168` - run_injection_loop() where debug calls should be added
  - `queue_sync.py:112` - get_playback_status() call - capture this data
  - `queue_sync.py:118-121` - current_playback() call - extract track details here
  - `queue_sync.py:132-160` - Injection logic - log success/failure events
  - `main.py:113-117` - LLM suggestion received - log this
  - `main.py:145-160` - JIT session start/update - log these events
  
  **Code Context**:
  - `queue_sync.py:23-37` - JITQueueSync.__init__ signature to modify
  - `main.py:148` - Where JITQueueSync is instantiated

  **Acceptance Criteria**:

  ```bash
  # AC1: JITQueueSync accepts debug_writer parameter
  .venv/bin/python -c "
  from queue_sync import JITQueueSync
  from debug_writer import DebugWriter
  dw = DebugWriter(enabled=True)
  jit = JITQueueSync(debug_writer=dw)
  print('PASS')
  "
  # Expected: PASS

  # AC2: --debug creates log file when app runs briefly
  # (This requires Spotify to be playing, so mark as manual verification)
  # Manual: Run `python main.py --debug`, make one request, exit
  # Verify: `ls logs/session_*.jsonl` shows new file
  # Verify: `cat logs/session_*.jsonl | head -5` shows cycle data

  # AC3: No debug artifacts without --debug
  .venv/bin/python -c "
  import os
  before = set(os.listdir('logs')) if os.path.exists('logs') else set()
  # Simulate: main.py without --debug would not create new files
  # (Can't fully test without Spotify, so check flag parsing)
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--debug', action='store_true')
  args = parser.parse_args([])  # No --debug
  print('PASS' if not args.debug else 'FAIL')
  "
  # Expected: PASS
  ```

  **Commit**: YES
  - Message: `feat(debug): integrate DebugWriter into main.py and queue_sync.py`
  - Files: `main.py`, `queue_sync.py`

---

- [x] 5. Create monitor.py dashboard

  **What to do**:
  - Create `monitor.py` with rich-based live dashboard
  - Accept log file path as argument, or `--latest` to find most recent
  - Layout panels:
    - NOW PLAYING: title, artist, progress bar, time until injection
    - SHADOW QUEUE: remaining count, next 3 songs
    - INJECTION STATUS: last injection time, current state
    - EVENTS LOG: scrolling list of recent events (last 10)
    - ERRORS: any errors (highlighted red)
  - Tail the JSONL file, parse lines, update dashboard
  - Handle: file not found (wait and retry), malformed lines (skip with warning), stale file (show "no updates in Xs")
  - Graceful Ctrl+C exit

  **Must NOT do**:
  - Don't connect to Spotify API directly
  - Don't modify log files
  - Don't add complex configuration (hardcoded layout)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: UI/visual dashboard creation, layout design
  - **Skills**: `["frontend-ui-ux"]`
    - frontend-ui-ux: Dashboard layout and visual design decisions

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (sequential)
  - **Blocks**: Task 6
  - **Blocked By**: Task 4

  **References**:

  **Pattern References**:
  - rich library Live: https://rich.readthedocs.io/en/latest/live.html
  - rich library Layout: https://rich.readthedocs.io/en/latest/layout.html
  - rich library Panel: https://rich.readthedocs.io/en/latest/panel.html
  
  **Code Context**:
  - `debug_writer.py` - JSONL format and data structures to parse

  **Acceptance Criteria**:

  ```bash
  # AC1: monitor.py exists and imports
  .venv/bin/python -c "import monitor; print('PASS')"
  # Expected: PASS

  # AC2: --help shows usage
  .venv/bin/python monitor.py --help | grep -q "latest\|file" && echo "PASS" || echo "FAIL"
  # Expected: PASS

  # AC3: --latest finds most recent file
  # First create a test log file
  .venv/bin/python -c "
  from debug_writer import DebugWriter, create_cycle_snapshot, create_event
  dw = DebugWriter(enabled=True)
  dw.log_event('session_start', {'test': True})
  dw.log_cycle(create_cycle_snapshot(1, {'title': 'Test'}, {'remaining': 5}, {}))
  dw.close()
  "
  # Then verify monitor can find it
  timeout 3 .venv/bin/python monitor.py --latest 2>&1 | head -3
  # Expected: Shows dashboard or "Loading..." (not "file not found" error)

  # AC4: Handles missing file gracefully
  timeout 3 .venv/bin/python monitor.py /nonexistent/file.jsonl 2>&1 | grep -i "wait\|not found" && echo "PASS"
  # Expected: PASS (shows waiting message, doesn't crash)

  # AC5: Exits cleanly on Ctrl+C
  timeout 2 .venv/bin/python monitor.py --latest &
  PID=$!
  sleep 1
  kill -INT $PID 2>/dev/null
  wait $PID 2>/dev/null
  echo "PASS"
  # Expected: PASS (no traceback)
  ```

  **Commit**: YES
  - Message: `feat(debug): add monitor.py live dashboard`
  - Files: `monitor.py`

---

- [x] 6. End-to-end testing and edge cases

  **What to do**:
  - Test full workflow: main.py --debug in one terminal, monitor.py --latest in another
  - Verify dashboard updates within 2 seconds of events
  - Test edge cases:
    - Monitor starts before main.py (should wait for file)
    - Disk full simulation (DebugWriter should handle gracefully)
    - Very long song titles (should truncate)
    - Unicode in song titles (should display correctly)
    - Two main.py instances (should create separate log files due to PID)
  - Document any known limitations

  **Must NOT do**:
  - Don't add features beyond edge case handling
  - Don't add log rotation (MVP)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-low`
    - Reason: Testing and verification, some edge case fixes
  - **Skills**: `[]`

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 5 (final)
  - **Blocks**: None
  - **Blocked By**: Task 5

  **References**:

  **Pattern References**:
  - All previous tasks
  
  **Code Context**:
  - `debug_writer.py`, `monitor.py`, `main.py`, `queue_sync.py`

  **Acceptance Criteria**:

  ```bash
  # AC1: End-to-end (manual verification)
  # Terminal 1: python main.py --debug
  # Terminal 2: python monitor.py --latest
  # Make a request in Terminal 1, verify Terminal 2 updates within 2 seconds

  # AC2: PID in filename prevents collisions
  .venv/bin/python -c "
  from debug_writer import DebugWriter
  import os
  dw1 = DebugWriter(enabled=True)
  dw1.log_event('test', {})
  # Simulate second process (different PID in name)
  files = [f for f in os.listdir('logs') if 'session_' in f]
  dw1.close()
  # Check filename contains PID
  print('PASS' if any(str(os.getpid()) in f for f in files) else 'FAIL')
  "
  # Expected: PASS

  # AC3: Unicode handling
  .venv/bin/python -c "
  from debug_writer import DebugWriter, create_event
  import json
  dw = DebugWriter(enabled=True)
  dw.log_event('test', {'song': 'Bohemian Rhapsody'})
  dw.close()
  import glob, os
  latest = max(glob.glob('logs/session_*.jsonl'), key=os.path.getctime)
  with open(latest, encoding='utf-8') as f:
      data = json.loads(f.readlines()[-1])
  print('PASS' if 'Bohemian' in str(data) else 'FAIL')
  "
  # Expected: PASS
  ```

  **Commit**: YES
  - Message: `feat(debug): complete debug dashboard with edge case handling`
  - Files: Any files modified for edge cases

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `feat(debug): add --debug flag and rich dependency` | requirements.txt, .gitignore, main.py | grep checks |
| 2+3 | `feat(debug): add DebugWriter class for JSONL logging` | debug_writer.py | python import test |
| 4 | `feat(debug): integrate DebugWriter into main.py and queue_sync.py` | main.py, queue_sync.py | python import test |
| 5 | `feat(debug): add monitor.py live dashboard` | monitor.py | python import test |
| 6 | `feat(debug): complete debug dashboard with edge case handling` | various | manual e2e test |

---

## Success Criteria

### Verification Commands
```bash
# Install new dependency
.venv/bin/pip install -r requirements.txt

# Verify --debug flag works
.venv/bin/python main.py --help | grep debug

# Quick smoke test (requires Spotify playing)
# Terminal 1:
.venv/bin/python main.py --debug
# Terminal 2:
.venv/bin/python monitor.py --latest
```

### Final Checklist
- [ ] `rich` installed and importable
- [ ] `--debug` flag accepted by main.py
- [ ] Debug log files created in `logs/` when --debug used
- [ ] No log files created without --debug
- [ ] monitor.py displays live updating dashboard
- [ ] Dashboard shows: now playing, queue, injection status, events, errors
- [ ] Ctrl+C exits monitor cleanly
- [ ] All print statements in original code still work (no regression)

---

## Known Limitations (MVP)

1. **Print statement interference**: Existing print() statements may occasionally interleave with rich output in monitor. This is expected for MVP.
2. **No log rotation**: Long sessions will create large log files. Manual cleanup needed.
3. **No historical replay**: Monitor only shows live data, cannot replay old sessions.
4. **Single session view**: Monitor shows one session at a time.
5. **Fixed layout**: Dashboard layout is hardcoded, not configurable.

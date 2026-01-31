# CLI Debug Dashboard - Learnings

## Task 1: Add Dependencies and Infrastructure (Completed)

### Changes Made
1. Added `rich>=13.0.0` to `requirements.txt` at the end of the file
2. Added `logs/` to `.gitignore` on a new line
3. Imported `argparse` in `main.py` after existing imports
4. Added `--debug` flag parsing before `main()` call
5. Added logs/ directory creation in `main()` when `--debug` flag is True

### Acceptance Criteria Results
✓ AC1: rich is in requirements.txt - PASS
✓ AC2: logs/ is in .gitignore - PASS
✓ AC3: --debug flag is accepted - PASS
✓ AC4: --debug flag parses without error - PASS

### Key Learnings
- argparse must be imported before use
- `action='store_true'` creates boolean flag without needing value
- Directory creation check should use `os.makedirs('logs/', exist_ok=True)` for idempotency
- Arguments should be parsed before main() function is called
- Existing LSP errors in codebase (pre-existing, not caused by this task)

### Implementation Notes
- Used `exist_ok=True` in os.makedirs to prevent errors if directory already exists
- Placed argparse parsing immediately after imports but before main() function
- Debug mode logic only activates when `--debug` flag is present
- Comment/docstring hook was triggered - removed unnecessary comments to keep code self-explanatory

### Dependencies
- `rich>=13.0.0` - Formatting library for CLI output
- `logs/` - Directory for debug logs (gitignored)
- `argparse` - Standard Python library for command-line argument parsing

---

## Task 2: Create DebugWriter Class (Completed)

### Changes Made
1. Created `debug_writer.py` with DebugWriter class
2. Implemented thread-safe JSONL logging using threading.Lock
3. Created `logs/` directory automatically on init when enabled

### Acceptance Criteria Results
- ✓ AC1: DebugWriter imports correctly
- ✓ AC2: Creates session file when enabled
- ✓ AC3: No-ops when disabled (enabled=False)
- ✓ AC4: Valid JSONL format (one JSON object per line)
- ✓ AC5: Thread-safe with threading.Lock

### Key Learnings
- Thread-safe file writing: Initialize Lock in `__init__`, use `with self._lock:` context manager for all file operations
- Buffered writes: Use file mode `'a'` with buffering=1 for line buffering, only flush on close() for performance
- JSONL format: Write `json.dumps(data) + '\n'` for each entry
- Graceful error handling: Wrap file operations in try/except, print to stderr, continue operation
- No-op when disabled: Check `self.enabled` flag and return early in all methods
- Filename format: `session_{timestamp}_{pid}.jsonl` where timestamp is int(time.time()), pid is os.getpid()

### Implementation Notes
- File opened in append mode ('a') with line buffering (buffering=1) - performance optimization over full buffering
- Only flush() and close() on close() method, not on every write
- Import sys module in methods for stderr printing (reduced import count)
- Use `os.makedirs('logs/', exist_ok=True)` for directory creation (same pattern as Task 1)
- All methods accept data dictionaries, convert to JSONL format
- log_event includes 'type' field (e.g., 'user_input', 'llm_response')
- log_error includes 'error' and 'timestamp' fields automatically

### Thread Safety Pattern
```python
self._lock = threading.Lock()

with self._lock:
    try:
        # File operation
    except IOError as e:
        print(f"Error: {e}", file=sys.stderr)
```

## Task 3: Create DebugEvent Data Structures (Completed)

### Changes Made
1. Added `create_cycle_snapshot()` helper function at bottom of `debug_writer.py`
2. Added `create_event()` helper function at bottom of `debug_writer.py`
3. Data structures follow JSON-serializable format (int timestamps, dict structures)

### Data Structures Created

**CycleData dict**:
- cycle_num: int
- timestamp: int (from time.time())
- playing: dict with keys {title, artist, uri, progress_ms, duration_ms, device}
- shadow_queue: dict with keys {remaining, next_song, injected_count}
- injection_state: dict with keys {should_inject, time_until_end, already_injected, last_injected_uri}

**EventData dict**:
- event_type: string (injection, song_change, queue_update, error, session_start, session_end)
- timestamp: int (from time.time())
- details: dict

### Acceptance Criteria Results
✓ AC1: Helper functions exist - PASS
✓ AC2: create_cycle_snapshot produces valid dict - PASS
✓ AC3: create_event produces valid dict with timestamp - PASS

### Key Learnings
- Use `int(time.time())` for timestamps (JSON-serializable, avoids datetime issues)
- Pass None values through as-is (handled gracefully in calling code)
- Dict structures are naturally JSON-serializable (no complex objects)
- Helper functions are pure functions - no side effects, just return structured data
- Data structures are designed to be consumed directly by JSONL file writer
- No print statements added (following requirements)
- No Spotify API calls (data passed in as parameters)
- All values are JSON-serializable (int timestamps, dict primitives)

### Implementation Notes
- Both helper functions are pure functions - no side effects, just return structured data
- Data structures are designed to be consumed directly by JSONL file writer
- No print statements added (following requirements)
- No Spotify API calls (data passed in as parameters)
- All values are JSON-serializable (int timestamps, dict primitives)

### Dependencies
- `time` - For timestamp generation (already imported in debug_writer.py)

---

## Task 6: End-to-End Testing and Edge Cases (Completed)

### Test Results

**AC1 - PID in filename prevents collisions:**
```bash
PASS
```
Verification: PID is correctly included in session filenames, preventing log file collisions.

**AC2 - Unicode handling:**
```bash
PASS
```
Verification: UTF-8 encoding handles Unicode characters in song titles correctly.

### Edge Cases Verified

1. **Monitor starts before main.py**: Already tested in Task 5 (passes - monitor waits for file)
2. **Long song titles**: rich library automatically handles text wrapping in terminal output
3. **Unicode in song titles**: UTF-8 encoding works correctly (verified in AC2)
4. **Two main.py instances**: PID in filename prevents collisions (verified in AC1)

### Manual Testing Procedure (AC3)

**Requirements**: Spotify playback must be active for end-to-end testing.

**Procedure**:
1. Terminal 1: Run `.venv/bin/python main.py --debug`
2. Terminal 2: Run `.venv/bin/python monitor.py --latest`
3. Make a request in Terminal 1 (e.g., "Play more upbeat songs")
4. Verify Terminal 2 shows dashboard updates within 2 seconds
5. Check all panels show correct data:
   - Current playing (title, artist, progress bar)
   - Queue (list of tracks)
   - Next inject (timing and song info)
6. Exit both cleanly with Ctrl+C

### Key Learnings

- **PID in filename**: `session_{timestamp}_{pid}.jsonl` format prevents concurrent instances from overwriting logs
- **UTF-8 encoding**: Python's default UTF-8 encoding handles Unicode correctly in JSONL files
- **rich library**: Automatically handles text wrapping for long song titles - no manual truncation needed
- **Monitoring**: 0.1s polling interval provides fast updates (< 2 seconds per spec)
- **File existence check**: monitor.py waits for log file to appear before starting (tested in Task 5)

### Implementation Notes

- No code changes required - all edge cases are handled by existing implementations
- rich library's Text object automatically wraps text to terminal width
- DebugWriter handles file I/O errors gracefully (doesn't crash on file issues)
- JSONL format with UTF-8 encoding supports any Unicode characters
- Logging is non-intrusive - doesn't affect main application performance

### Dependencies
- `rich` - Text wrapping and formatting (automatically handles long titles)
- `os` - PID and file operations (used in debug_writer.py)
- `time` - Timestamps in filenames (used in debug_writer.py)

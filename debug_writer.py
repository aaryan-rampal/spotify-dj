"""
Thread-safe JSONL logging for debugging Spotify DJ sessions.

Provides a DebugWriter class that writes structured debug data to a JSONL file.
Thread-safe operations using threading.Lock for concurrent access.
"""

import json
import time
import os
import threading


class DebugWriter:
    """Thread-safe JSONL debug logger for Spotify DJ sessions."""

    def __init__(self, enabled=True):
        """
        Initialize the debug writer.

        Args:
            enabled: If True, creates log file and starts writing. If False, all methods are no-ops.
        """
        self.enabled = enabled
        self._lock = threading.Lock()
        self._file = None

        if self.enabled:
            os.makedirs("logs/", exist_ok=True)
            timestamp = int(time.time())
            pid = os.getpid()
            filename = f"logs/session_{timestamp}_{pid}.jsonl"
            self._file = open(filename, "a", buffering=1)

    def log_cycle(self, data):
        """
        Log a cycle data entry.

        Args:
            data: Dictionary with cycle information (cycle number, timestamps, queue stats, etc.)
        """
        if not self.enabled:
            return

        with self._lock:
            try:
                self._file.write(json.dumps(data) + "\n")
            except IOError as e:
                print(f"Error writing cycle log: {e}", file=__import__("sys").stderr)

    def log_event(self, event_type, data):
        """
        Log an event entry.

        Args:
            event_type: Type of event (e.g., 'user_input', 'llm_response', 'spotify_sync')
            data: Dictionary with event details
        """
        if not self.enabled:
            return

        with self._lock:
            try:
                entry = {"type": event_type, "data": data}
                self._file.write(json.dumps(entry) + "\n")
            except IOError as e:
                print(f"Error writing event log: {e}", file=__import__("sys").stderr)

    def log_error(self, error):
        """
        Log an error entry.

        Args:
            error: Error object or string to log
        """
        if not self.enabled:
            return

        with self._lock:
            try:
                entry = {
                    "type": "error",
                    "error": str(error) if not isinstance(error, str) else error,
                    "timestamp": time.time(),
                }
                self._file.write(json.dumps(entry) + "\n")
            except IOError as e:
                print(f"Error writing error log: {e}", file=__import__("sys").stderr)

    def close(self):
        """Close the log file and flush any buffered data."""
        if not self.enabled:
            return

        with self._lock:
            if self._file:
                try:
                    self._file.flush()
                    self._file.close()
                except IOError as e:
                    print(f"Error closing log file: {e}", file=__import__("sys").stderr)
                finally:
                    self._file = None


def create_cycle_snapshot(cycle_num, playing, shadow_queue, injection_state):
    """
    Create a snapshot of the current DJ session state.

    Args:
        cycle_num (int): Current cycle number
        playing (dict): Current playing track with keys: title, artist, uri, progress_ms, duration_ms, device
        shadow_queue (dict): Shadow queue state with keys: remaining, next_song, injected_count
        injection_state (dict): Injection state with keys: should_inject, time_until_end, already_injected, last_injected_uri

    Returns:
        dict: JSON-serializable cycle snapshot data
    """
    return {
        "cycle_num": cycle_num,
        "timestamp": int(time.time()),
        "playing": playing,
        "shadow_queue": shadow_queue,
        "injection_state": injection_state,
    }


def create_event(event_type, details):
    """
    Create an event entry for the debug log.

    Args:
        event_type (str): Type of event (injection, song_change, queue_update, error, session_start, session_end)
        details (dict): Event-specific details

    Returns:
        dict: JSON-serializable event data
    """
    return {"event_type": event_type, "timestamp": int(time.time()), "details": details}

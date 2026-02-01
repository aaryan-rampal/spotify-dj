"""
Just-In-Time (JIT) queue synchronization engine.
Maintains a shadow queue and injects songs at the right moment.
"""

import time
import threading
from spotify_client import SpotifyClient
from queue_manager import QueueManager
from config import JITConfig
from debug_writer import create_cycle_snapshot


class JITQueueSync:
    """
    Just-In-Time queue synchronization using polling and strategic injection.

    Instead of clearing and re-adding the queue, this system:
    1. Starts playback with the first song
    2. Polls Spotify playback status regularly
    3. Injects the next song 10-20 seconds before current song ends
    4. Allows mid-session queue updates
    """

    def __init__(self, spotify_client=None, debug_writer=None):
        """
        Initialize JIT queue sync engine.

        Args:
            spotify_client (SpotifyClient, optional): Existing SpotifyClient instance.
                                                      If None, a new one will be created.
            debug_writer (DebugWriter, optional): Debug logger instance for logging events.
        """
        self.client = spotify_client or SpotifyClient()
        self.queue_manager = None
        self.running = False
        self.injection_thread = None
        self.last_injected_uri = None
        self.last_played_uri = (
            None  # Track currently playing song to detect when it changes
        )
        self.already_injected_for_current = (
            False  # Flag to ensure only one injection per song
        )
        self.debug_writer = debug_writer

    def start_dj_session(self, initial_queue):
        """
        Start a DJ session with initial queue.

        Args:
            initial_queue (list): List of dicts with format [{"title": "...", "artist": "..."}, ...]

        Returns:
            bool: True if session started successfully, False otherwise
        """
        if not initial_queue:
            print("Error: Cannot start DJ session with empty queue")
            return False

        print(f"Starting DJ session with {len(initial_queue)} songs...")

        # Create queue manager and convert all songs to URIs
        self.queue_manager = QueueManager(initial_queue, self.client)

        if self.queue_manager.is_empty():
            print("Error: No valid songs found in initial queue")
            return False

        # Get first song and start playback
        first_uri = self.queue_manager.get_next_track_uri()
        if not first_uri:
            print("Error: Could not get first track URI")
            return False

        print("Starting playback with first song...")
        if not self.client.start_playback(first_uri):
            print("Error: Failed to start playback")
            return False

        self.last_injected_uri = first_uri
        print(
            f"✓ Playback started, {self.queue_manager.queue_length()} songs queued for injection"
        )
        return True

    def run_injection_loop(self, max_duration_seconds=None):
        """
        Main polling/injection loop (runs in thread).

        This loop:
        - Checks if playback is active
        - Polls Spotify status at POLL_INTERVAL
        - Injects next song when INJECTION_THRESHOLD seconds remain
        - Handles errors gracefully
        - Stops when queue is exhausted or playback ends

        Args:
            max_duration_seconds (int, optional): Maximum session duration in seconds.
                                                  If None, runs until queue empty or playback stops.
        """
        if self.queue_manager is None:
            print("Error: No queue manager initialized. Call start_dj_session() first.")
            return

        self.running = True
        start_time = time.time()

        print(
            f"Starting injection loop with threshold={JITConfig.INJECTION_THRESHOLD}s, "
            f"poll_interval={JITConfig.POLL_INTERVAL}s"
        )

        try:
            cycle_num = 0
            while self.running:
                # Check timeout
                if max_duration_seconds is not None:
                    elapsed = time.time() - start_time
                    if elapsed > max_duration_seconds:
                        print(f"Session timeout ({max_duration_seconds}s) reached")
                        break

                # Check if playback is active
                status = self.client.get_playback_status()
                if status is None or not status.get("is_playing"):
                    print("Playback stopped or no active playback")
                    break

                # Detect if the currently playing song has changed
                current_playback = self.client.sp.current_playback()
                current_uri = None
                if current_playback and current_playback.get("item"):
                    current_uri = current_playback["item"].get("uri")

                # If song has changed, reset injection flag
                if current_uri and current_uri != self.last_played_uri:
                    if self.debug_writer:
                        self.debug_writer.log_event(
                            "song_change",
                            {"uri": current_uri, "from_uri": self.last_played_uri},
                        )
                    self.last_played_uri = current_uri
                    self.already_injected_for_current = False

                # Sleep for poll interval
                time.sleep(JITConfig.POLL_INTERVAL)

                # Log cycle snapshot
                if self.debug_writer:
                    playing = {}
                    status = self.client.get_playback_status()
                    if status and status.get("is_playing"):
                        track = status.get("item")
                        if track:
                            playing = {
                                "title": track.get("name", ""),
                                "artist": track["artists"][0].get("name", "")
                                if track.get("artists")
                                else "",
                                "uri": track.get("uri", ""),
                                "progress_ms": status.get("progress_ms", 0),
                                "duration_ms": track.get("duration_ms", 0),
                                "device": status.get("device", "") or "",
                            }

                    shadow_queue = {
                        "remaining": self.queue_manager.queue_length()
                        if self.queue_manager
                        else 0,
                        "next_song": None,
                        "injected_count": 0,
                    }
                    if self.queue_manager and not self.queue_manager.is_empty():
                        next_song_data = self.queue_manager.peek_next_song()
                        if next_song_data:
                            shadow_queue["next_song"] = (
                                f"{next_song_data[0]} by {next_song_data[1]}"
                            )

                    injection_state = {
                        "should_inject": self.client.should_inject_next(),
                        "time_until_end": self.client.calculate_time_until_end(),
                        "already_injected": self.already_injected_for_current,
                        "last_injected_uri": self.last_injected_uri,
                    }

                    cycle_snapshot = create_cycle_snapshot(
                        cycle_num=cycle_num,
                        playing=playing,
                        shadow_queue=shadow_queue,
                        injection_state=injection_state,
                    )
                    self.debug_writer.log_cycle(cycle_snapshot)

                    cycle_num += 1

                # Check if we should inject next song (and haven't already for this song)
                if (
                    self.client.should_inject_next()
                    and not self.already_injected_for_current
                ):
                    if self.queue_manager.is_empty():
                        print("Queue exhausted, ending session")
                        break

                    next_uri = self.queue_manager.get_next_track_uri()
                    if not next_uri:
                        print("No more songs to inject")
                        break

                    # Try to inject with retries
                    injected = False
                    for attempt in range(JITConfig.RETRY_ATTEMPTS):
                        time_left = self.client.calculate_time_until_end()
                        if self.client.inject_next_song(next_uri):
                            print(f"✓ Injected song (remaining: {time_left:.1f}s)")
                            if self.debug_writer:
                                self.debug_writer.log_event(
                                    "injection",
                                    {"uri": next_uri, "time_left": time_left},
                                )
                            self.queue_manager.get_next_song()  # Pop from queue
                            self.last_injected_uri = next_uri
                            self.already_injected_for_current = (
                                True  # Mark as injected for this song
                            )
                            injected = True
                            break
                        else:
                            if attempt < JITConfig.RETRY_ATTEMPTS - 1:
                                print(
                                    f"  Retry {attempt + 1}/{JITConfig.RETRY_ATTEMPTS}..."
                                )
                                time.sleep(JITConfig.RETRY_DELAY)

                    if not injected:
                        print(
                            f"✗ Failed to inject song after {JITConfig.RETRY_ATTEMPTS} attempts"
                        )
                        if self.debug_writer:
                            self.debug_writer.log_event(
                                "injection_failed",
                                {"uri": next_uri, "attempts": JITConfig.RETRY_ATTEMPTS},
                            )
                        # Continue anyway, will try again

        except KeyboardInterrupt:
            print("\nSession interrupted by user")
        except Exception as e:
            print(f"Error in injection loop: {e}")
            if self.debug_writer:
                self.debug_writer.log_error(e)
        finally:
            self.running = False
            print("Injection loop ended")

    def update_shadow_queue(self, new_songs_list):
        """
        Update the shadow queue immediately (while loop is running).

        Allows users to change mood/genre mid-session.
        Next injection will use songs from updated queue.

        Args:
            new_songs_list (list): New list of dicts with format [{"title": "...", "artist": "..."}, ...]
        """
        if self.queue_manager is None:
            print("Error: No DJ session active")
            return False

        print(f"Updating shadow queue with {len(new_songs_list)} new songs...")
        self.queue_manager.update_queue(new_songs_list)
        if self.debug_writer:
            self.debug_writer.log_event(
                "queue_update", {"new_count": len(new_songs_list)}
            )
        print(
            f"✓ Shadow queue updated, {self.queue_manager.queue_length()} songs queued"
        )
        return True

    def stop_session(self):
        """
        Stop the injection loop cleanly.
        """
        print("Stopping DJ session...")
        self.running = False

    def start_injection_thread(self, max_duration_seconds=None):
        """
        Start the injection loop in a background thread.

        Args:
            max_duration_seconds (int, optional): Maximum session duration in seconds.

        Returns:
            threading.Thread: The injection thread
        """
        self.injection_thread = threading.Thread(
            target=self.run_injection_loop, args=(max_duration_seconds,), daemon=False
        )
        self.injection_thread.start()
        return self.injection_thread

    def wait_for_session(self):
        """
        Wait for the injection thread to complete.
        """
        if self.injection_thread:
            self.injection_thread.join()


# Legacy QueueSync class for compatibility
class QueueSync:
    """
    Legacy queue sync class (maintained for compatibility).

    For new code, use JITQueueSync instead.
    This class now uses the JIT system internally.
    """

    def __init__(self, spotify_client=None):
        """
        Initialize the queue sync engine.

        Args:
            spotify_client (SpotifyClient, optional): Existing SpotifyClient instance.
        """
        self.client = spotify_client or SpotifyClient()
        self.jit_sync = JITQueueSync(self.client)

    def sync_queue(self, desired_queue):
        """
        Synchronize queue using JIT system (legacy interface).

        Args:
            desired_queue (list): List of dicts with format [{"title": "...", "artist": "..."}, ...]

        Returns:
            dict: Statistics about the sync operation
        """
        result = {
            "cleared": False,
            "added": 0,
            "failed": 0,
            "total": len(desired_queue),
        }

        if not desired_queue:
            print("Desired queue is empty. Skipping sync.")
            return result

        if self.jit_sync.start_dj_session(desired_queue):
            result["added"] = self.jit_sync.queue_manager.queue_length()
        else:
            result["failed"] = len(desired_queue)

        return result

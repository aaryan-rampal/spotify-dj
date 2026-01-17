"""
Spotify client for queue management and playback control.
"""
import os
import time
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import JITConfig


class SpotifyClient:
    """Client for interacting with Spotify's queue and playback APIs."""

    def __init__(self):
        """Initialize Spotify client with credentials from environment variables."""
        load_dotenv()

        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

        if not client_id or not client_secret or not redirect_uri:
            raise ValueError(
                "Missing Spotify credentials. Please set SPOTIFY_CLIENT_ID, "
                "SPOTIFY_CLIENT_SECRET, and SPOTIFY_REDIRECT_URI in .env file."
            )

        # Scope needed for queue operations and playback control
        scope = "user-read-playback-state,user-modify-playback-state"

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
            )
        )

    def get_current_queue(self):
        """
        Fetch the current user's queue from Spotify.

        Returns:
            list: List of dicts with format [{"title": "song name", "artist": "artist name"}, ...]
                  Includes currently playing track followed by queued tracks.
        """
        queue_items = []

        # Get currently playing track
        current = self.sp.currently_playing()
        if current and current.get("item"):
            track = current["item"]
            queue_items.append({
                "title": track["name"],
                "artist": track["artists"][0]["name"] if track.get("artists") else "Unknown Artist"
            })

        # Get the queue
        queue = self.sp.queue()
        if queue and queue.get("queue"):
            for track in queue["queue"]:
                queue_items.append({
                    "title": track["name"],
                    "artist": track["artists"][0]["name"] if track.get("artists") else "Unknown Artist"
                })

        return queue_items

    def search_track(self, title, artist):
        """
        Search for a track on Spotify given title and artist.

        Args:
            title (str): Track title
            artist (str): Artist name

        Returns:
            str: Spotify track URI if found, None otherwise
        """
        try:
            query = f"{title} {artist}"
            results = self.sp.search(q=query, type="track", limit=1)

            if results and results.get("tracks") and results["tracks"].get("items"):
                track = results["tracks"]["items"][0]
                return track["uri"]
            else:
                return None
        except Exception as e:
            print(f"Error searching for track '{title}' by '{artist}': {e}")
            return None

    def clear_queue(self):
        """
        Stub for queue clearing - not applicable with JIT system.

        The JIT (Just-In-Time) queue injection system eliminates the need to clear queues.
        Instead of clearing and re-adding, we inject songs strategically as they're needed.

        Returns:
            bool: False (not used in JIT system)
        """
        print("Note: clear_queue() is not used in JIT system. Using injection instead.")
        return False

    def start_playback(self, track_uri):
        """
        Start playing a specific track, clearing queue and starting new playback.

        Args:
            track_uri (str): Spotify track URI to start playing

        Raises:
            Exception: If no active device or Spotify API error

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            devices = self.sp.devices()
            if not devices or not devices.get("devices"):
                raise Exception("No active Spotify device found")

            active_device = None
            for device in devices["devices"]:
                if device.get("is_active"):
                    active_device = device
                    break

            if not active_device:
                active_device = devices["devices"][0]

            self.sp.start_playback(device_id=active_device["id"], uris=[track_uri])
            return True
        except Exception as e:
            print(f"Error starting playback: {e}")
            return False

    def get_playback_status(self):
        """
        Get current playback status including progress and duration.

        Returns:
            dict: {"is_playing": bool, "progress_ms": int, "duration_ms": int, "device": str}
                  Returns dict with all values as None/empty if no playback active

        Returns:
            None if error occurred
        """
        try:
            playback = self.sp.current_playback()
            if not playback:
                return {"is_playing": False, "progress_ms": 0, "duration_ms": 0, "device": None}

            if not playback.get("item"):
                return {"is_playing": False, "progress_ms": 0, "duration_ms": 0, "device": None}

            return {
                "is_playing": playback.get("is_playing", False),
                "progress_ms": playback.get("progress_ms", 0),
                "duration_ms": playback["item"].get("duration_ms", 0),
                "device": playback.get("device", {}).get("name", "Unknown")
            }
        except Exception as e:
            print(f"Error getting playback status: {e}")
            return None

    def calculate_time_until_end(self):
        """
        Calculate seconds remaining until current track ends.

        Returns:
            float: Seconds until end of current track, or -1 if no playback
        """
        status = self.get_playback_status()
        if status is None or not status.get("is_playing"):
            return -1

        progress_ms = status.get("progress_ms", 0)
        duration_ms = status.get("duration_ms", 0)

        if duration_ms <= 0:
            return -1

        time_remaining_ms = duration_ms - progress_ms
        if time_remaining_ms < 0:
            return 0

        return time_remaining_ms / 1000.0

    def should_inject_next(self):
        """
        Check if it's time to inject the next song.

        Returns True if time remaining <= INJECTION_THRESHOLD seconds.

        Returns:
            bool: True if injection should happen now, False otherwise
        """
        try:
            time_until_end = self.calculate_time_until_end()
            if time_until_end < 0:
                return False

            return time_until_end <= JITConfig.INJECTION_THRESHOLD
        except Exception as e:
            print(f"Error checking injection timing: {e}")
            return False

    def inject_next_song(self, track_uri):
        """
        Inject the next song into the queue.

        Args:
            track_uri (str): Spotify track URI to inject

        Returns:
            bool: True if injection succeeded, False otherwise (no exception raised)
        """
        try:
            self.sp.add_to_queue(track_uri)
            return True
        except Exception as e:
            print(f"Error injecting song {track_uri}: {e}")
            return False

    def add_songs_to_queue(self, songs_list):
        """
        Add songs to the user's queue.

        Args:
            songs_list (list): List of dicts with format [{"title": "...", "artist": "..."}, ...]

        Returns:
            dict: Statistics about the operation
                  {"added": count, "failed": count, "total": count}
        """
        stats = {"added": 0, "failed": 0, "total": len(songs_list)}

        if not songs_list:
            print("No songs to add to queue.")
            return stats

        for song in songs_list:
            title = song.get("title")
            artist = song.get("artist")

            if not title or not artist:
                print(f"Warning: Skipping song with missing title or artist: {song}")
                stats["failed"] += 1
                continue

            # Search for the track
            track_uri = self.search_track(title, artist)

            if track_uri:
                try:
                    self.sp.add_to_queue(track_uri)
                    print(f"✓ Added '{title}' by {artist}")
                    stats["added"] += 1
                except Exception as e:
                    print(f"✗ Failed to add '{title}' by {artist}: {e}")
                    stats["failed"] += 1
            else:
                print(f"✗ Could not find '{title}' by {artist} on Spotify")
                stats["failed"] += 1

        return stats


# Test script - uncomment to run manually
"""
if __name__ == "__main__":
    # Initialize the client
    client = SpotifyClient()

    # Fetch and print the current queue
    print("Fetching current queue from Spotify...")
    queue = client.get_current_queue()

    if queue:
        print(f"\nFound {len(queue)} track(s) in queue:\n")
        for i, track in enumerate(queue, 1):
            status = "(Currently Playing)" if i == 1 else f"(Position {i-1} in queue)"
            print(f"{i}. {track['title']} by {track['artist']} {status}")
    else:
        print("\nNo tracks currently playing or in queue.")
"""

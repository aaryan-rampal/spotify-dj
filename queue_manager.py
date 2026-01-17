"""
Queue manager for shadow queue tracking and song injection.
Maintains the "shadow queue" in Python and provides next song for injection.
Thread-safe implementation using locks to prevent race conditions.
"""
import threading
from spotify_client import SpotifyClient


class QueueManager:
    """
    Manages a shadow queue of songs to be injected into Spotify playback.
    Thread-safe implementation using threading.Lock() to synchronize access.
    """

    def __init__(self, songs_list, spotify_client=None):
        """
        Initialize with list of songs and convert to Spotify track URIs.

        Args:
            songs_list (list): List of dicts with format [{"title": "...", "artist": "..."}, ...]
            spotify_client (SpotifyClient, optional): Existing SpotifyClient instance.
                                                      If None, a new one will be created.
        """
        self.client = spotify_client or SpotifyClient()
        self.songs_with_uris = []
        self.current_index = 0
        self._lock = threading.Lock()  # Lock for thread-safe access

        # Convert all songs to URIs immediately
        for song in songs_list:
            title = song.get("title")
            artist = song.get("artist")

            if not title or not artist:
                print(f"Warning: Skipping song with missing title or artist: {song}")
                continue

            # Search for track URI
            track_uri = self.client.search_track(title, artist)

            if track_uri:
                self.songs_with_uris.append({
                    "title": title,
                    "artist": artist,
                    "uri": track_uri
                })
            else:
                print(f"Warning: Could not find '{title}' by '{artist}' on Spotify")

    def update_queue(self, new_songs_list):
        """
        Update shadow queue with new songs (mid-session changes).
        Thread-safe: uses lock to prevent race conditions with injection loop.
        Preserves current position in queue.

        Args:
            new_songs_list (list): New list of dicts with format [{"title": "...", "artist": "..."}, ...]
        """
        with self._lock:
            self.songs_with_uris = []
            self.current_index = 0

            for song in new_songs_list:
                title = song.get("title")
                artist = song.get("artist")

                if not title or not artist:
                    print(f"Warning: Skipping song with missing title or artist: {song}")
                    continue

                track_uri = self.client.search_track(title, artist)

                if track_uri:
                    self.songs_with_uris.append({
                        "title": title,
                        "artist": artist,
                        "uri": track_uri
                    })
                else:
                    print(f"Warning: Could not find '{title}' by '{artist}' on Spotify")

    def get_next_song(self):
        """
        Pop and return next song tuple (title, artist) or None if empty.
        Thread-safe: uses lock.

        Returns:
            tuple: (title, artist) or None if no more songs
        """
        with self._lock:
            if self.current_index >= len(self.songs_with_uris):
                return None

            song = self.songs_with_uris[self.current_index]
            self.current_index += 1
            return (song["title"], song["artist"])

    def peek_next_song(self):
        """
        Look at next song without removing it.
        Thread-safe: uses lock.

        Returns:
            tuple: (title, artist) or None if no more songs
        """
        with self._lock:
            if self.current_index >= len(self.songs_with_uris):
                return None

            song = self.songs_with_uris[self.current_index]
            return (song["title"], song["artist"])

    def get_next_track_uri(self):
        """
        Get the Spotify URI of the next song to inject (already searched).
        Thread-safe: uses lock.

        Returns:
            str: Spotify track URI or None if no more songs
        """
        with self._lock:
            if self.current_index >= len(self.songs_with_uris):
                return None

            return self.songs_with_uris[self.current_index]["uri"]

    def is_empty(self):
        """
        Check if queue has more songs.
        Thread-safe: uses lock.

        Returns:
            bool: True if no more songs in queue
        """
        with self._lock:
            return self.current_index >= len(self.songs_with_uris)

    def queue_length(self):
        """
        Get number of songs remaining in shadow queue (not yet injected).
        Thread-safe: uses lock.

        Returns:
            int: Number of remaining songs
        """
        with self._lock:
            return max(0, len(self.songs_with_uris) - self.current_index)

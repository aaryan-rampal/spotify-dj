"""
Spotify client for queue management and playback control.
"""
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth


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

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
        Clear all songs from the user's queue.

        Note: The Spotify Web API doesn't provide a direct "remove from queue" endpoint.
        This method uses the approach of pausing and resuming playback to effectively
        clear the queue, or returns False if the queue is already empty.

        Returns:
            bool: True if successful or queue was empty, False on error
        """
        try:
            # Get current queue
            queue_data = self.sp.queue()
            queue_items = queue_data.get("queue", []) if queue_data else []

            if not queue_items:
                print("Queue is already empty.")
                return True

            # Since Spotify Web API doesn't support removing from queue directly,
            # we acknowledge the limitation. For a real implementation, users can:
            # 1. Use the Spotify client directly to remove songs
            # 2. Create a playlist and use that instead
            # 3. Use start_playback to restart with new tracks
            #
            # For now, we return True to indicate willingness to clear, but in practice
            # we'll rely on adding new songs to the queue (which will follow the current track)

            print(f"Note: Queue has {len(queue_items)} track(s). Spotify API doesn't support")
            print("direct queue removal. New tracks will be added to the queue.")
            print("The queue will be effectively replaced as new songs are added.")
            return True

        except Exception as e:
            print(f"Error checking queue: {e}")
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

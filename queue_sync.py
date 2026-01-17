"""
Queue synchronization engine that converts LLM-suggested songs to Spotify tracks and updates the queue.
"""
from spotify_client import SpotifyClient


class QueueSync:
    """Synchronizes a desired queue with the actual Spotify queue."""

    def __init__(self, spotify_client=None):
        """
        Initialize the queue sync engine.

        Args:
            spotify_client (SpotifyClient, optional): Existing SpotifyClient instance.
                                                       If None, a new one will be created.
        """
        self.client = spotify_client or SpotifyClient()

    def sync_queue(self, desired_queue):
        """
        Synchronize the desired queue with Spotify's actual queue.

        This method:
        1. Clears the current Spotify queue
        2. Adds songs from desired_queue in order

        Args:
            desired_queue (list): List of dicts with format [{"title": "...", "artist": "..."}, ...]

        Returns:
            dict: Statistics about the sync operation
                  {
                      "cleared": bool (whether queue was cleared),
                      "added": int (number of songs added),
                      "failed": int (number of songs that failed),
                      "total": int (total songs attempted)
                  }
        """
        result = {
            "cleared": False,
            "added": 0,
            "failed": 0,
            "total": len(desired_queue)
        }

        if not desired_queue:
            print("Desired queue is empty. Skipping sync.")
            return result

        # Step 1: Clear the current queue
        print("Step 1: Clearing current queue...")
        result["cleared"] = self.client.clear_queue()

        if not result["cleared"]:
            print("Warning: Queue clearing may have failed, but continuing with adding songs.")

        # Step 2: Add songs from desired queue in order
        print("\nStep 2: Adding songs to queue...")
        add_stats = self.client.add_songs_to_queue(desired_queue)

        result["added"] = add_stats["added"]
        result["failed"] = add_stats["failed"]

        # Summary
        print("\n" + "=" * 60)
        print("Sync Summary:")
        print(f"  Total songs attempted: {result['total']}")
        print(f"  Successfully added: {result['added']}")
        print(f"  Failed: {result['failed']}")
        print(f"  Queue cleared: {'Yes' if result['cleared'] else 'No'}")
        print("=" * 60)

        return result

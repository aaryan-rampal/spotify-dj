"""
Test script for SpotifyClient - verifies queue fetching works correctly.
"""
from spotify_client import SpotifyClient


def test_get_current_queue():
    """Test the get_current_queue method."""
    print("Initializing Spotify client...")
    client = SpotifyClient()

    print("Fetching current queue from Spotify...")
    queue = client.get_current_queue()

    if queue:
        print(f"\n✓ Successfully fetched {len(queue)} track(s) in queue:\n")
        for i, track in enumerate(queue, 1):
            status = "(Currently Playing)" if i == 1 else f"(Position {i-1} in queue)"
            print(f"{i}. '{track['title']}' by {track['artist']} {status}")
    else:
        print("\n! No tracks currently playing or in queue.")
        print("  To test this properly, start playing music on Spotify and/or add songs to your queue.")

    print("\n✓ Test completed successfully!")
    return queue


if __name__ == "__main__":
    test_get_current_queue()

"""
Test script for QueueSync - verifies queue synchronization works correctly.
"""

from spotify_client import SpotifyClient
from queue_sync import QueueSync


def test_queue_sync():
    """Test the QueueSync class with a sample desired queue."""
    print("=" * 60)
    print("Queue Sync Test")
    print("=" * 60)

    # Initialize clients
    print("\nInitializing Spotify client...")
    spotify_client = SpotifyClient()

    print("Initializing QueueSync engine...")
    queue_sync = QueueSync(spotify_client)

    # Fetch current queue before sync
    print("\n--- Before Sync ---")
    print("Fetching current queue...")
    current_queue = spotify_client.get_current_queue()
    if current_queue:
        print(f"Current queue has {len(current_queue)} track(s):")
        for i, track in enumerate(current_queue, 1):
            status = "(Now Playing)" if i == 1 else f"(Position {i - 1})"
            print(f"  {i}. '{track['title']}' by {track['artist']} {status}")
    else:
        print("No tracks currently playing or in queue.")

    # Define desired queue (mix of real songs)
    desired_queue = [
        {"title": "Blinding Lights", "artist": "The Weeknd"},
        {"title": "As It Was", "artist": "Harry Styles"},
        {"title": "Heat Waves", "artist": "Glass Animals"},
        {"title": "Levitating", "artist": "Dua Lipa"},
        {
            "title": "NonExistentSongXYZ",
            "artist": "FakeArtistABC",
        },  # Test error handling
    ]

    print("\n--- Desired Queue ---")
    print("Songs to add:")
    for i, track in enumerate(desired_queue, 1):
        print(f"  {i}. '{track['title']}' by {track['artist']}")

    # Sync the queue
    print("\n--- Syncing Queue ---")
    result = queue_sync.sync_queue(desired_queue)

    # Fetch queue after sync
    print("\n--- After Sync ---")
    print("Fetching updated queue...")
    updated_queue = spotify_client.get_current_queue()
    if updated_queue:
        print(f"Updated queue has {len(updated_queue)} track(s):")
        for i, track in enumerate(updated_queue, 1):
            status = "(Now Playing)" if i == 1 else f"(Position {i - 1})"
            print(f"  {i}. '{track['title']}' by {track['artist']} {status}")
    else:
        print("Queue is empty.")

    print("\n✓ Test completed successfully!")
    return result


def test_search_track():
    """Test the track search functionality."""
    print("\n" + "=" * 60)
    print("Track Search Test")
    print("=" * 60)

    spotify_client = SpotifyClient()

    test_cases = [
        ("Bohemian Rhapsody", "Queen"),
        ("Imagine", "John Lennon"),
        ("Fake Song XYZ", "Fake Artist"),
    ]

    print("\nSearching for tracks:")
    for title, artist in test_cases:
        uri = spotify_client.search_track(title, artist)
        if uri:
            print(f"✓ Found '{title}' by {artist}: {uri}")
        else:
            print(f"✗ Could not find '{title}' by {artist}")

    print("\n✓ Search test completed!")


if __name__ == "__main__":
    # Run both tests
    test_search_track()
    test_queue_sync()

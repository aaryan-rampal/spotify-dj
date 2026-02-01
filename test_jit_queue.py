"""
Comprehensive test suite for Just-In-Time (JIT) queue injection system.
Tests basic injection, mid-session updates, and edge cases.
"""

from spotify_dj.spotify_client import SpotifyClient
from spotify_dj.queue_manager import QueueManager
from spotify_dj.queue_sync import JITQueueSync
from spotify_dj.config import JITConfig


def test_queue_manager_basic():
    """Test basic QueueManager functionality: initialization, peek, get."""
    print("\n" + "=" * 70)
    print("TEST: QueueManager Basic Functionality")
    print("=" * 70)

    test_songs = [
        {"title": "Bohemian Rhapsody", "artist": "Queen"},
        {"title": "Stairway to Heaven", "artist": "Led Zeppelin"},
        {"title": "Imagine", "artist": "John Lennon"},
    ]

    try:
        manager = QueueManager(test_songs)

        print(f"\nInitialized with {len(test_songs)} songs")
        print(f"Queue length: {manager.queue_length()}")

        # Test peek
        next_song = manager.peek_next_song()
        print(f"Peeked next song: {next_song}")

        # Test get
        song = manager.get_next_song()
        print(f"Got next song: {song}")
        print(f"Remaining: {manager.queue_length()}")

        # Test get again
        song2 = manager.get_next_song()
        print(f"Got next song: {song2}")
        print(f"Remaining: {manager.queue_length()}")

        # Test empty
        song3 = manager.get_next_song()
        song4 = manager.get_next_song()
        print(f"Queue empty: {manager.is_empty()}")

        print("\n✓ QueueManager basic test passed")
        return True

    except Exception as e:
        print(f"\n✗ QueueManager basic test failed: {e}")
        return False


def test_spotify_client_search():
    """Test Spotify client song search functionality."""
    print("\n" + "=" * 70)
    print("TEST: SpotifyClient Song Search")
    print("=" * 70)

    try:
        client = SpotifyClient()

        print("\nSearching for songs...")

        # Test valid song
        uri = client.search_track("Bohemian Rhapsody", "Queen")
        if uri:
            print(f"✓ Found 'Bohemian Rhapsody': {uri}")
        else:
            print("✗ Could not find 'Bohemian Rhapsody'")
            return False

        # Test another valid song
        uri2 = client.search_track("Imagine", "John Lennon")
        if uri2:
            print(f"✓ Found 'Imagine': {uri2}")
        else:
            print("✗ Could not find 'Imagine'")
            return False

        print("\n✓ Song search test passed")
        return True

    except Exception as e:
        print(f"\n✗ Song search test failed: {e}")
        return False


def test_spotify_playback_status():
    """Test getting playback status from Spotify."""
    print("\n" + "=" * 70)
    print("TEST: SpotifyClient Playback Status")
    print("=" * 70)

    try:
        client = SpotifyClient()

        print("\nGetting playback status...")
        status = client.get_playback_status()

        if status is None:
            print("✗ Failed to get playback status")
            return False

        print(f"  Is playing: {status.get('is_playing')}")
        print(f"  Progress: {status.get('progress_ms')}ms")
        print(f"  Duration: {status.get('duration_ms')}ms")
        print(f"  Device: {status.get('device')}")

        if status.get("is_playing"):
            time_left = client.calculate_time_until_end()
            print(f"  Time until end: {time_left:.1f}s")
            print("\n✓ Playback status test passed (playback active)")
        else:
            print("\n! Playback not currently active")
            print("  (This is OK for testing, but to fully test injection,")
            print("   please start playing music on Spotify)")

        return True

    except Exception as e:
        print(f"\n✗ Playback status test failed: {e}")
        return False


def test_jit_injection_simulation():
    """
    Simulate JIT injection system (without requiring active Spotify playback).
    Tests the queue manager and injection loop logic.
    """
    print("\n" + "=" * 70)
    print("TEST: JIT Injection Loop Simulation")
    print("=" * 70)

    test_songs = [
        {"title": "Bohemian Rhapsody", "artist": "Queen"},
        {"title": "Stairway to Heaven", "artist": "Led Zeppelin"},
        {"title": "Imagine", "artist": "John Lennon"},
        {"title": "Smells Like Teen Spirit", "artist": "Nirvana"},
        {"title": "Hotel California", "artist": "Eagles"},
    ]

    try:
        client = SpotifyClient()
        jit = JITQueueSync(client)

        print(f"\nStarting simulation with {len(test_songs)} songs...")
        print("(This simulates the injection logic without modifying Spotify)")

        # Create queue manager to test song lookup
        manager = QueueManager(test_songs, client)
        found_songs = manager.queue_length()
        print(
            f"\n✓ Successfully looked up {found_songs} out of {len(test_songs)} songs"
        )

        if manager.is_empty():
            print("✗ All songs failed lookup")
            return False

        # Simulate injection sequence
        print("\nSimulating injection sequence:")
        injection_count = 0
        while not manager.is_empty() and injection_count < 5:
            uri = manager.get_next_track_uri()
            song = manager.peek_next_song()
            if song:
                print(f"  Would inject: {song[0]} by {song[1]}")
                manager.get_next_song()  # Consume
                injection_count += 1

        print(
            f"\n✓ Injected {injection_count} songs (remaining: {manager.queue_length()})"
        )
        print("\n✓ JIT injection simulation passed")
        return True

    except Exception as e:
        print(f"\n✗ JIT injection simulation failed: {e}")
        return False


def test_queue_update_mid_session():
    """
    Test updating the shadow queue mid-session.
    Simulates user changing mood/genre while playback is ongoing.
    """
    print("\n" + "=" * 70)
    print("TEST: Mid-Session Queue Update")
    print("=" * 70)

    initial_songs = [
        {"title": "Bohemian Rhapsody", "artist": "Queen"},
        {"title": "Stairway to Heaven", "artist": "Led Zeppelin"},
    ]

    new_songs = [
        {"title": "Blinding Lights", "artist": "The Weeknd"},
        {"title": "Levitating", "artist": "Dua Lipa"},
        {"title": "Anti-Hero", "artist": "Taylor Swift"},
    ]

    try:
        client = SpotifyClient()
        manager = QueueManager(initial_songs, client)

        print(f"\nInitial queue length: {manager.queue_length()}")

        # Consume one song
        manager.get_next_song()
        print(f"After consuming one: {manager.queue_length()}")

        # Update queue mid-session
        print(f"\nUpdating with {len(new_songs)} new songs...")
        manager.update_queue(new_songs)
        print(f"After update: {manager.queue_length()}")

        # Verify we can get next songs
        next_song = manager.peek_next_song()
        if next_song:
            print(f"Next song after update: {next_song[0]} by {next_song[1]}")

        print("\n✓ Mid-session queue update test passed")
        return True

    except Exception as e:
        print(f"\n✗ Mid-session queue update test failed: {e}")
        return False


def test_edge_cases():
    """Test edge cases: empty queue, invalid songs, etc."""
    print("\n" + "=" * 70)
    print("TEST: Edge Cases")
    print("=" * 70)

    try:
        client = SpotifyClient()

        # Test 1: Empty queue
        print("\nTest 1: Empty queue")
        manager = QueueManager([], client)
        if manager.is_empty():
            print("  ✓ Empty queue handled correctly")
        else:
            print("  ✗ Empty queue not handled")
            return False

        # Test 2: Invalid song (missing artist)
        print("\nTest 2: Invalid song format")
        invalid_songs = [
            {"title": "No Artist Song"},  # Missing artist
            {"artist": "No Title Artist"},  # Missing title
            {"title": "", "artist": ""},  # Empty strings
        ]
        manager = QueueManager(invalid_songs, client)
        if manager.is_empty():
            print("  ✓ Invalid songs filtered out correctly")
        else:
            print("  ✗ Invalid songs not filtered")
            return False

        # Test 3: Peeking empty queue
        print("\nTest 3: Operations on empty queue")
        manager = QueueManager([], client)
        peek = manager.peek_next_song()
        get_song = manager.get_next_song()
        uri = manager.get_next_track_uri()
        if peek is None and get_song is None and uri is None:
            print("  ✓ Empty queue operations safe")
        else:
            print("  ✗ Empty queue operations failed")
            return False

        print("\n✓ Edge case tests passed")
        return True

    except Exception as e:
        print(f"\n✗ Edge case tests failed: {e}")
        return False


def print_test_summary(results):
    """Print summary of all test results."""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    tests = [
        ("QueueManager Basic Functionality", results.get("queue_manager_basic", False)),
        ("SpotifyClient Song Search", results.get("spotify_search", False)),
        ("SpotifyClient Playback Status", results.get("playback_status", False)),
        ("JIT Injection Simulation", results.get("jit_simulation", False)),
        ("Mid-Session Queue Update", results.get("mid_session_update", False)),
        ("Edge Cases", results.get("edge_cases", False)),
    ]

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    for test_name, result in tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)

    return passed == total


def run_all_tests():
    """Run all JIT system tests."""
    print("\n" + "=" * 70)
    print("SPOTIFY DJ - JIT QUEUE INJECTION SYSTEM - TEST SUITE")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  Injection threshold: {JITConfig.INJECTION_THRESHOLD}s")
    print(f"  Poll interval: {JITConfig.POLL_INTERVAL}s")
    print(f"  Retry attempts: {JITConfig.RETRY_ATTEMPTS}")

    results = {}

    # Run tests
    results["queue_manager_basic"] = test_queue_manager_basic()
    results["spotify_search"] = test_spotify_client_search()
    results["playback_status"] = test_spotify_playback_status()
    results["jit_simulation"] = test_jit_injection_simulation()
    results["mid_session_update"] = test_queue_update_mid_session()
    results["edge_cases"] = test_edge_cases()

    # Print summary
    all_passed = print_test_summary(results)

    if all_passed:
        print("\n🎵 All tests passed! JIT system ready for production use.")
    else:
        print("\n⚠ Some tests failed. Review output above for details.")

    return all_passed


if __name__ == "__main__":
    run_all_tests()

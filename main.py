"""
Main CLI loop for Spotify DJ application.
Integrates SpotifyClient, LLMClient, JITQueueSync, and ConversationHistory.
"""

import sys
from spotify_client import SpotifyClient
from llm_client import LLMClient
from queue_sync import JITQueueSync
from conversation import ConversationHistory
import argparse


def display_welcome():
    """Display welcome message to the user."""
    print("\n" + "=" * 60)
    print("🎵  Welcome to Spotify DJ!")
    print("=" * 60)
    print("Tell me what you'd like to listen to - describe your mood,")
    print("suggest a genre, or ask for specific songs.")
    print("\nExamples:")
    print("  'I want some upbeat indie rock'")
    print("  'Switch to chill lo-fi beats'")
    print("  'Add some jazz'")
    print("\nType 'exit', 'quit', or 'bye' to leave.")
    print("=" * 60 + "\n")


def should_exit(user_input):
    """Check if user wants to exit."""
    exit_keywords = {"exit", "quit", "bye", "stop"}
    return user_input.strip().lower() in exit_keywords


def format_queue_for_display(queue):
    """Format queue for display to user."""
    if not queue:
        return "Queue is empty"

    lines = []
    for i, song in enumerate(queue[:5], 1):  # Show first 5 songs
        title = song.get("title", "Unknown")
        artist = song.get("artist", "Unknown Artist")
        lines.append(f"  {i}. {title} by {artist}")

    if len(queue) > 5:
        lines.append(f"  ... and {len(queue) - 5} more songs")

    return "\n".join(lines)


def main():
    """Main CLI loop for Spotify DJ."""
    print("Spotify DJ starting...")

    # Initialize components
    try:
        print("Initializing Spotify client...")
        spotify_client = SpotifyClient()

        print("Initializing LLM client...")
        llm_client = LLMClient()

        conversation_history = ConversationHistory()
        jit_sync = None
        jit_started = False

        print("✓ All components initialized\n")
    except ValueError as e:
        print(f"✗ Initialization Error: {e}")
        print("Please check your .env file and make sure all credentials are set.")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected Error: {e}")
        sys.exit(1)

    display_welcome()

    # Main loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                print("(Please enter a message or type 'exit' to quit)")
                continue

            # Check if user wants to exit
            if should_exit(user_input):
                print("\n" + "=" * 60)
                print("Thanks for using Spotify DJ! Enjoy the music! 🎵")
                print("=" * 60)
                break

            # Fetch current queue from Spotify
            print("\nFetching current queue from Spotify...")
            try:
                current_queue = spotify_client.get_current_queue()
                print(f"✓ Current queue has {len(current_queue)} song(s)")
                if current_queue:
                    print("Currently playing:")
                    print(
                        f"  {current_queue[0]['title']} by {current_queue[0]['artist']}"
                    )
            except Exception as e:
                print(f"✗ Error fetching queue: {e}")
                print("Make sure Spotify is playing on your device")
                continue

            # Add user message to history
            conversation_history.add_user_message(user_input)

            # Get LLM suggestion
            print("Getting song suggestions from LLM...")
            try:
                suggested_queue = llm_client.get_queue_suggestion(
                    conversation_history=conversation_history.get_history(),
                    current_queue=current_queue,
                    user_message=user_input,
                )

                if not suggested_queue:
                    print("✗ LLM returned an empty queue. Please try again.")
                    # Remove the user message from history since we're retrying
                    conversation_history.messages.pop()
                    continue

                print(f"✓ LLM suggested {len(suggested_queue)} song(s)")
            except ValueError as e:
                print(f"✗ Error parsing LLM response: {e}")
                # Remove the user message from history since we're retrying
                conversation_history.messages.pop()
                continue
            except Exception as e:
                print(f"✗ LLM API Error: {e}")
                # Remove the user message from history since we're retrying
                conversation_history.messages.pop()
                continue

            # Store LLM response in history
            # We'll store a summary of the queue suggestion
            queue_summary = f"Suggested {len(suggested_queue)} songs"
            conversation_history.add_assistant_response(queue_summary)

            # Start or update JIT queue
            print("Updating queue with new songs...")
            try:
                if not jit_started:
                    # First time - start DJ session
                    print("Starting DJ session...")
                    jit_sync = JITQueueSync(spotify_client)

                    if not jit_sync.start_dj_session(suggested_queue):
                        print("✗ Failed to start DJ session")
                        # Remove messages from history
                        conversation_history.messages.pop()
                        conversation_history.messages.pop()
                        continue

                    # Start injection loop in background thread
                    jit_sync.start_injection_thread()
                    jit_started = True
                    print("✓ DJ session started, injection loop running in background")
                else:
                    # Update existing session
                    if not jit_sync.update_shadow_queue(suggested_queue):
                        print("✗ Failed to update queue")
                        # Remove messages from history
                        conversation_history.messages.pop()
                        conversation_history.messages.pop()
                        continue
                    print("✓ Queue updated with new suggestions")

            except Exception as e:
                print(f"✗ Error updating queue: {e}")
                # Remove messages from history
                conversation_history.messages.pop()
                conversation_history.messages.pop()
                continue

            # Display feedback
            print("\nQueue preview:")
            print(format_queue_for_display(suggested_queue))
            print()

        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("Spotify DJ interrupted. Goodbye! 🎵")
            print("=" * 60)
            break
        except Exception as e:
            print(f"\n✗ Unexpected Error: {e}")
            print("Please try again or type 'exit' to quit.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Spotify DJ - Conversational music queue manager"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    if args.debug:
        import os

        os.makedirs("logs/", exist_ok=True)

    main()

"""
Test script for LLMClient.
"""
import json
from llm_client import LLMClient


def test_llm_client():
    """Test the LLMClient with a sample request."""
    print("Initializing LLMClient...")
    try:
        client = LLMClient()
    except ValueError as e:
        print(f"Error initializing client: {e}")
        print("Please ensure OPENROUTER_API_KEY is set in .env file.")
        return

    # Sample conversation history
    conversation_history = [
        {"role": "user", "content": "I want to listen to some music"},
        {"role": "assistant", "content": "Sure! What kind of mood are you in?"},
    ]

    # Sample current queue
    current_queue = [
        {"title": "Blinding Lights", "artist": "The Weeknd"},
        {"title": "levitating", "artist": "Dua Lipa"},
    ]

    # User message
    user_message = "Make it more upbeat and indie-focused"

    print("\nSending request to OpenRouter API...")
    print(f"User message: {user_message}")
    print(f"Current queue: {json.dumps(current_queue, indent=2)}")

    try:
        suggested_queue = client.get_queue_suggestion(
            conversation_history, current_queue, user_message
        )

        print("\nSuggested queue from LLM:")
        print(json.dumps(suggested_queue, indent=2))

        # Validate the structure
        assert isinstance(suggested_queue, list), "Queue should be a list"
        for item in suggested_queue:
            assert isinstance(item, dict), "Each item should be a dict"
            assert "title" in item, "Each item should have a 'title'"
            assert "artist" in item, "Each item should have an 'artist'"

        print("\n✓ Queue structure is valid!")
        print(f"✓ Returned {len(suggested_queue)} songs")

    except Exception as e:
        print(f"Error getting queue suggestion: {e}")
        raise


if __name__ == "__main__":
    test_llm_client()

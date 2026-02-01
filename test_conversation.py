"""
Test script for ConversationHistory class.
Verifies that conversation management works correctly.
"""

from conversation import ConversationHistory


def test_conversation_history():
    """Test ConversationHistory functionality."""
    print("Testing ConversationHistory class...\n")

    # Test 1: Create instance and verify empty
    print("Test 1: Initialize empty conversation")
    conv = ConversationHistory()
    assert conv.get_history() == [], "History should be empty on init"
    print("✓ Empty history initialized correctly\n")

    # Test 2: Add user messages
    print("Test 2: Add user messages")
    conv.add_user_message("I want upbeat jazz")
    conv.add_user_message("More energetic please")
    history = conv.get_history()
    assert len(history) == 2, "Should have 2 messages"
    assert history[0]["role"] == "user", "First message should be user role"
    assert history[0]["content"] == "I want upbeat jazz", (
        "First message content mismatch"
    )
    assert history[1]["role"] == "user", "Second message should be user role"
    assert history[1]["content"] == "More energetic please", (
        "Second message content mismatch"
    )
    print("✓ User messages added correctly\n")

    # Test 3: Add assistant responses
    print("Test 3: Add assistant responses")
    conv.add_assistant_response("Here's a jazz queue with upbeat tracks")
    conv.add_assistant_response("Updated queue with more energetic jazz tracks")
    history = conv.get_history()
    assert len(history) == 4, "Should have 4 messages total"
    assert history[2]["role"] == "assistant", "Third message should be assistant role"
    assert history[2]["content"] == "Here's a jazz queue with upbeat tracks"
    assert history[3]["role"] == "assistant", "Fourth message should be assistant role"
    assert history[3]["content"] == "Updated queue with more energetic jazz tracks"
    print("✓ Assistant responses added correctly\n")

    # Test 4: Verify chronological order
    print("Test 4: Verify chronological order")
    # Messages were added as: user, user, assistant, assistant
    expected_order = [
        ("user", "I want upbeat jazz"),
        ("user", "More energetic please"),
        ("assistant", "Here's a jazz queue with upbeat tracks"),
        ("assistant", "Updated queue with more energetic jazz tracks"),
    ]
    history = conv.get_history()
    for i, (expected_role, expected_content) in enumerate(expected_order):
        assert history[i]["role"] == expected_role, f"Message {i} role mismatch"
        assert history[i]["content"] == expected_content, (
            f"Message {i} content mismatch"
        )
    print("✓ Messages are in correct chronological order\n")

    # Test 5: Test clear()
    print("Test 5: Test clear() resets history")
    conv.clear()
    assert conv.get_history() == [], "History should be empty after clear()"
    print("✓ History cleared successfully\n")

    # Test 6: Verify get_history() returns a copy
    print("Test 6: Verify get_history() returns independent copy")
    conv.add_user_message("Test message")
    history1 = conv.get_history()
    history1.append({"role": "user", "content": "Malicious addition"})
    history2 = conv.get_history()
    assert len(history2) == 1, "History should not be modified by external changes"
    print("✓ get_history() returns independent copy\n")

    # Test 7: Test format matches LLM API expectation
    print("Test 7: Verify format matches LLM API expectation")
    conv.clear()
    conv.add_user_message("I like classical music")
    conv.add_assistant_response(
        '{"queue": [{"title": "Symphony No. 5", "artist": "Beethoven"}]}'
    )
    history = conv.get_history()

    # Check that format is exactly what LLM API expects
    for msg in history:
        assert isinstance(msg, dict), "Each message should be a dict"
        assert "role" in msg, "Each message must have 'role' field"
        assert "content" in msg, "Each message must have 'content' field"
        assert msg["role"] in ["user", "assistant"], (
            "Role must be 'user' or 'assistant'"
        )
        assert isinstance(msg["content"], str), "Content must be a string"

    print("✓ Format matches LLM API expectations\n")

    print("=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)


if __name__ == "__main__":
    test_conversation_history()

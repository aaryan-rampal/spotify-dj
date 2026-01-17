"""
Test JSON extraction from various LLM response formats.
"""
from llm_client import LLMClient


def test_json_extraction():
    """Test JSON extraction with different formats."""
    client = LLMClient()

    test_cases = [
        ("Raw JSON array", '[{"title": "Song 1", "artist": "Artist 1"}]'),
        ("JSON object with queue key", '{"queue": [{"title": "Song 1", "artist": "Artist 1"}]}'),
        ("JSON in markdown code block", '```json\n[{"title": "Song 1", "artist": "Artist 1"}]\n```'),
        ("JSON with descriptive text", 'Here is the queue:\n\n```json\n[{"title": "Song 1", "artist": "Artist 1"}]\n```\n\nEnjoy!'),
    ]

    all_passed = True
    for name, test_case in test_cases:
        try:
            result = client._extract_json_from_response(test_case)
            assert "queue" in result
            assert isinstance(result["queue"], list)
            assert len(result["queue"]) > 0
            print(f"✓ {name}: Successfully extracted and normalized queue")
        except Exception as e:
            print(f"✗ {name}: {e}")
            all_passed = False

    return all_passed


if __name__ == "__main__":
    if test_json_extraction():
        print("\n✓ All JSON extraction tests passed!")
    else:
        print("\n✗ Some tests failed")
        exit(1)

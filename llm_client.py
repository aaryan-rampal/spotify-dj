"""
LLM Client for OpenRouter API integration.
Provides queue suggestions based on user input and current queue state.
"""
import os
import json
import requests
from dotenv import load_dotenv


class LLMClient:
    """Client for interacting with OpenRouter API to get queue suggestions."""

    def __init__(self, api_key=None):
        """
        Initialize LLM client with OpenRouter API key.

        Args:
            api_key (str, optional): OpenRouter API key. If not provided, loads from environment.

        Raises:
            ValueError: If API key is not provided and not found in environment.
        """
        if api_key is None:
            load_dotenv()
            api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise ValueError(
                "Missing OpenRouter API key. Please set OPENROUTER_API_KEY in .env file "
                "or pass it as an argument."
            )

        self.api_key = api_key
        self.api_endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def _get_system_prompt(self):
        """
        Get the system prompt for the DJ curator LLM.

        Returns:
            str: System prompt instructions for the LLM.
        """
        return """You are a DJ curator assistant. Your job is to help users manage their Spotify queue based on their requests.

When a user sends a message, you will:
1. Receive the current queue state as JSON
2. Receive their request (mood, genre, specific songs, etc.)
3. Suggest a new queue that fulfills their request

IMPORTANT: You must ALWAYS respond with valid JSON in exactly this format:
{"queue": [{"title": "Song Name", "artist": "Artist Name"}, {"title": "Another Song", "artist": "Another Artist"}]}

The queue should be an array of songs with "title" and "artist" fields. You can:
- Keep some existing songs if they fit the request
- Add new song suggestions
- Reorder songs
- Remove songs

Be creative and suggest songs that match the user's mood or preference. Always respond with valid JSON only - no other text."""

    def get_queue_suggestion(self, conversation_history, current_queue, user_message):
        """
        Get a queue suggestion from the LLM based on user input and current queue state.

        Args:
            conversation_history (list): List of dicts with format:
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            current_queue (list): Current queue as list of dicts:
                [{"title": "Song Name", "artist": "Artist Name"}, ...]
            user_message (str): The user's new request/message.

        Returns:
            list: Suggested queue as list of dicts:
                [{"title": "Song Name", "artist": "Artist Name"}, ...]

        Raises:
            ValueError: If the response is not valid JSON or missing required fields.
            requests.RequestException: If the API call fails.
        """
        # Build the messages for the API call
        messages = []

        # Add conversation history
        messages.extend(conversation_history)

        # Add current queue context and user message
        context_message = f"""Current Queue:
{json.dumps(current_queue, indent=2)}

User Request: {user_message}"""

        messages.append({"role": "user", "content": context_message})

        # Make the API call
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "openrouter/auto",  # Use auto-routing to pick the best available model
            "messages": messages,
            "system": self._get_system_prompt(),
        }

        response = requests.post(
            self.api_endpoint,
            headers=headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        # Parse the response
        response_data = response.json()
        assistant_message = response_data["choices"][0]["message"]["content"]

        # Extract JSON from the response
        queue_json = self._extract_json_from_response(assistant_message)

        return queue_json["queue"]

    def _extract_json_from_response(self, response_text):
        """
        Extract and validate JSON from LLM response.

        Args:
            response_text (str): The LLM's response text.

        Returns:
            dict: Parsed JSON with format {"queue": [...]}

        Raises:
            ValueError: If the response doesn't contain valid JSON in the expected format.
        """
        import re

        # Try to parse the entire response as JSON first
        try:
            queue_json = json.loads(response_text)
            queue_json = self._normalize_queue_response(queue_json)
            self._validate_queue_structure(queue_json)
            return queue_json
        except (json.JSONDecodeError, ValueError):
            pass

        # Try to extract JSON from markdown code blocks (```json...```)
        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", response_text, re.DOTALL)
        if json_match:
            try:
                queue_json = json.loads(json_match.group(1))
                queue_json = self._normalize_queue_response(queue_json)
                self._validate_queue_structure(queue_json)
                return queue_json
            except (json.JSONDecodeError, ValueError):
                pass

        # Try to find raw JSON object or array in the response
        json_match = re.search(r"(\{.*\}|\[.*\])", response_text, re.DOTALL)
        if json_match:
            try:
                queue_json = json.loads(json_match.group(1))
                queue_json = self._normalize_queue_response(queue_json)
                self._validate_queue_structure(queue_json)
                return queue_json
            except (json.JSONDecodeError, ValueError):
                pass

        raise ValueError(
            f"Could not extract valid JSON from LLM response: {response_text}"
        )

    def _normalize_queue_response(self, data):
        """
        Normalize the queue response to the expected format.

        Handles both direct array format and {"queue": [...]} format.

        Args:
            data: The parsed JSON data.

        Returns:
            dict: Normalized queue data in {"queue": [...]} format.
        """
        if isinstance(data, list):
            # If it's already a list of songs, wrap it in the queue format
            return {"queue": data}
        elif isinstance(data, dict) and "queue" in data:
            # Already in the expected format
            return data
        else:
            # Unexpected format
            return {"queue": []}

    def _validate_queue_structure(self, queue_json):
        """
        Validate the queue structure.

        Args:
            queue_json (dict): The queue data to validate.

        Raises:
            ValueError: If the structure is invalid.
        """
        if not isinstance(queue_json, dict) or "queue" not in queue_json:
            raise ValueError(
                f"Response JSON missing 'queue' field. Got: {queue_json}"
            )

        if not isinstance(queue_json["queue"], list):
            raise ValueError(
                f"'queue' field must be a list. Got: {type(queue_json['queue'])}"
            )

        # Validate each queue item
        for item in queue_json["queue"]:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Queue items must be dicts. Got: {type(item)}"
                )
            if "title" not in item or "artist" not in item:
                raise ValueError(
                    f"Queue item missing 'title' or 'artist': {item}"
                )

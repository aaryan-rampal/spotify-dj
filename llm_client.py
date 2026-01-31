"""
LLM Client for OpenRouter API integration.
Provides queue suggestions based on user input and current queue state.
"""

import json
import requests
from config import LLMConfig


class LLMClient:
    """Client for interacting with OpenRouter API to get queue suggestions."""

    def __init__(self, api_key=None):
        """
        Initialize LLM client with OpenRouter API key.

        Args:
            api_key (str, optional): OpenRouter API key. If not provided, loads from config.

        Raises:
            ValueError: If API key is not provided and not found in config.
        """
        if api_key is None:
            api_key = LLMConfig.get_api_key()

        self.api_key = api_key
        self.api_endpoint = LLMConfig.API_ENDPOINT
        self.model = LLMConfig.get_model()
        self.timeout = LLMConfig.get_timeout()

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

IMPORTANT:
- You must ALWAYS respond with valid JSON in exactly this format:
  {"queue": [{"title": "Song Name", "artist": "Artist Name"}, {"title": "Another Song", "artist": "Another Artist"}]}
- Your entire response must be a single JSON object. No markdown. No code fences. No extra keys.
- Do not ask clarifying questions. If the request is ambiguous, make a reasonable best-guess.
- If you cannot comply, return an empty queue: {"queue": []}

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
        system_message = {"role": "system", "content": self._get_system_prompt()}

        # Prepend a system message unless the caller already provided one.
        if not conversation_history or conversation_history[0].get("role") != "system":
            messages.append(system_message)

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
            "model": self.model,
            "messages": messages,
            # OpenRouter JSON mode: guarantees the assistant message is valid JSON.
            # Docs: https://openrouter.ai/docs/api/reference/parameters
            "response_format": {"type": "json_object"},
        }

        response = requests.post(
            self.api_endpoint,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code != 200:
            print(f"DEBUG: API Response Status: {response.status_code}")
            print(f"DEBUG: Response Headers: {response.headers}")
            print(f"DEBUG: Response Body: {response.text}")
            print(f"DEBUG: Request Payload: {payload}")

        response.raise_for_status()

        # Parse the response
        try:
            response_data = response.json()
        except ValueError as e:
            body = response.text
            snippet = body if len(body) <= 2000 else body[:2000] + "..."
            raise ValueError(
                f"OpenRouter returned non-JSON response (status={response.status_code}): {snippet}"
            ) from e

        # TODO: Validate response schema more robustly
        # TODO: add LLM reasoning to debug logs
        try:
            assistant_message = response_data["choices"][0]["message"]["content"]
        except Exception as e:
            raise ValueError(
                f"Unexpected OpenRouter response schema; expected choices[0].message.content. Got keys: {list(response_data.keys())}"
            ) from e

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
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            parsed = None

        if parsed is not None:
            queue_json = self._normalize_queue_response(parsed)
            self._validate_queue_structure(queue_json)
            return queue_json

        # Try to extract JSON from markdown code blocks (```json...```)
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            try:
                queue_json = json.loads(json_match.group(1))
                queue_json = self._normalize_queue_response(queue_json)
                self._validate_queue_structure(queue_json)
                return queue_json
            except (json.JSONDecodeError, ValueError):
                pass

        # Try to locate the first valid JSON object/array substring.
        decoder = json.JSONDecoder()
        for i, ch in enumerate(response_text):
            if ch not in "{[":
                continue
            try:
                parsed, _ = decoder.raw_decode(response_text[i:])
            except json.JSONDecodeError:
                continue

            queue_json = self._normalize_queue_response(parsed)
            self._validate_queue_structure(queue_json)
            return queue_json

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
        if isinstance(data, dict) and "queue" in data:
            # Already in the expected format
            return data

        raise ValueError(
            f"Unexpected JSON format; expected {{'queue': [...]}}. Got: {type(data)}"
        )

    def _validate_queue_structure(self, queue_json):
        """
        Validate the queue structure.

        Args:
            queue_json (dict): The queue data to validate.

        Raises:
            ValueError: If the structure is invalid.
        """
        if not isinstance(queue_json, dict) or "queue" not in queue_json:
            raise ValueError(f"Response JSON missing 'queue' field. Got: {queue_json}")

        if not isinstance(queue_json["queue"], list):
            raise ValueError(
                f"'queue' field must be a list. Got: {type(queue_json['queue'])}"
            )

        # Validate each queue item
        for item in queue_json["queue"]:
            if not isinstance(item, dict):
                raise ValueError(f"Queue items must be dicts. Got: {type(item)}")
            if "title" not in item or "artist" not in item:
                raise ValueError(f"Queue item missing 'title' or 'artist': {item}")

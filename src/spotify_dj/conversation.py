"""
Conversation History Management.
Stores and manages user and assistant messages throughout a session.
"""


class ConversationHistory:
    """Manages conversation history formatted for LLM API consumption."""

    def __init__(self):
        """Initialize empty conversation list."""
        self.messages = []

    def add_user_message(self, text):
        """
        Add a user message to the conversation history.

        Args:
            text (str): The user's message content.
        """
        self.messages.append({"role": "user", "content": text})

    def add_assistant_response(self, text):
        """
        Add an assistant response to the conversation history.

        Args:
            text (str): The assistant's response content.
        """
        self.messages.append({"role": "assistant", "content": text})

    def get_history(self):
        """
        Get the full conversation history in format suitable for LLM API.

        Returns:
            list: List of dicts with format:
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
                in chronological order.
        """
        return self.messages.copy()

    def clear(self):
        """Reset conversation history to empty."""
        self.messages = []

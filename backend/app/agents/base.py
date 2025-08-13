"""
Base classes / adapters for agents so we can stream consistently.
"""

from typing import Generator

class AgentBase:
    """Optional base class; agents can inherit this if you want."""
    def get_response(self, message: str) -> str:
        raise NotImplementedError("Agent must implement get_response()")

    def stream_response(self, message: str):
        """
        Optional: If your agent can *natively* stream, implement this
        and yield small strings (tokens, words, sentences).
        """
        # Default implementation: just yield the full response once.
        yield self.get_response(message)


def streaming_adapter(agent) -> Generator[str, None, None]:
    """
    Turn any agent into a streaming generator.
    Prefer agent.stream_response(); else chunk get_response() words.
    """
    if hasattr(agent, "stream_response") and callable(agent.stream_response):
        yield from agent.stream_response  # type: ignore
    else:
        text = agent.get_response("")
        words = text.split()
        CHUNK = 15
        for i in range(0, len(words), CHUNK):
            yield " ".join(words[i:i + CHUNK])
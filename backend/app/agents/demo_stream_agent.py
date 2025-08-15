"""
Demo streaming agent that simulates typing by yielding words one by one.
Useful for testing WebSocket streaming in development.
"""

import time
from typing import Generator

class DemoStreamAgent:
    def __init__(self):
        self.name = "demo_stream"

    def stream_response(self, message: str) -> Generator[str, None, None]:
        """
        Yield a fake reply word-by-word with short pauses
        so the frontend can show a typing effect.
        """
        words = [
            "Hello,", "this", "is", "a", "demo", "streaming", "agent.",
            "You", "said:", message
        ]
        for word in words:
            yield word + " "
            time.sleep(0.3)  # simulate delay per word
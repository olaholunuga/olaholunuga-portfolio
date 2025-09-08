from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import json
import requests
from flask_cors import CORS


# load_dotenv()


# # app = Flask(__name__)
# # CORS(app)


class BaseAgent:
    """
    Base class for AI agents in the portfolio project.
    Supports both non-streaming and streaming completions from Groq's API.
    """

    def __init__(self, name, description):
        """
        :param name: Agent display name
        :param description: Short description of the agent's role
        """
        self.name = name
        self.description = description
        self.api_key = os.getenv("GROQ_API_KEY")

    # -----------------------------
    # Non-streaming completions
    # -----------------------------
    def get_response(self, prompt):
        """
        Returns the full completion result from the Groq API in one call.
        :param prompt: The user's message
        :return: Full string response
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "llama3-8b-8192",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are {self.name}, {self.description}. Respond in a helpful, concise, and professional manner."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"An error occurred: {str(e)}"

    # -----------------------------
    # Streaming completions
    # -----------------------------
    def stream_response(self, prompt):
        """
        Generator that yields chunks of the assistant's response in real-time.
        :param prompt: The user's message
        :yield: Text chunks from the model's output
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "llama3-8b-8192",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are {self.name}, {self.description}. Respond in a helpful, concise, and professional manner."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500,
                "stream": True  # ✅ Enable streaming
            }

            with requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                stream=True
            ) as r:

                if r.status_code != 200:
                    yield f"Error: {r.status_code} - {r.text}"
                    return

                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if line.startswith("data:"):
                        payload = line[len("data:"):].strip()
                        if payload == "[DONE]":
                            break
                        try:
                            parsed = json.loads(payload)
                            delta = parsed["choices"][0]["delta"]
                            if "content" in delta:
                                yield delta["content"]
                        except Exception as e:
                            yield f"[Stream Parse Error: {str(e)}]"

        except Exception as e:
            yield f"An error occurred during streaming: {str(e)}"
"""Shared LLM client for target agents (Groq)."""

import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def get_client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set (check your .env file)")
    return Groq(api_key=key)


def chat(messages: list[dict], tools: list[dict] | None = None, model: str | None = None):
    kwargs = {"model": model or DEFAULT_MODEL, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    return get_client().chat.completions.create(**kwargs)

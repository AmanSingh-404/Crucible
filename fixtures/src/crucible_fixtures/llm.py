"""Shared LLM client for target agents (Groq)."""

import os

import groq
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MAX_ATTEMPTS = 3


class ModelOutputError(RuntimeError):
    """The model kept producing output the API could not parse (e.g. a malformed tool call)."""


def get_client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set (check your .env file)")
    return Groq(api_key=key)


def chat(messages: list[dict], tools: list[dict] | None = None, model: str | None = None):
    kwargs = {"model": model or DEFAULT_MODEL, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    last_error = None
    for _ in range(MAX_ATTEMPTS):
        try:
            return get_client().chat.completions.create(**kwargs)
        except groq.BadRequestError as exc:
            last_error = exc
    raise ModelOutputError(str(last_error)) from last_error

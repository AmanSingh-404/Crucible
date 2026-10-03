"""Shared LLM client for target agents (Groq)."""

import os
import re
import time

import groq
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
MAX_ATTEMPTS = 3
MAX_RATE_LIMIT_RETRIES = 5


class ModelOutputError(RuntimeError):
    """The model kept producing output the API could not parse (e.g. a malformed tool call)."""


def get_client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set (check your .env file)")
    return Groq(api_key=key)


def _extract_retry_seconds(error: groq.RateLimitError, default: float = 5.0) -> float:
    """Groq's 429 message gives either 'try again in 5.34s' (per-minute limit)
    or 'try again in 9m37.584s' (daily limit, minutes+seconds combined)."""
    match = re.search(r"try again in (?:(\d+)m)?([\d.]+)s", str(error))
    if not match:
        return default
    minutes = float(match.group(1)) if match.group(1) else 0.0
    seconds = float(match.group(2))
    return minutes * 60 + seconds + 1.0


def chat(messages: list[dict], tools: list[dict] | None = None, model: str | None = None):
    kwargs = {"model": model or DEFAULT_MODEL, "messages": messages}
    if tools:
        kwargs["tools"] = tools

        rate_limit_retries = 0
    last_error = None

    while True:
        for _ in range(MAX_ATTEMPTS):
            try:
                return get_client().chat.completions.create(**kwargs)
            except groq.RateLimitError as exc:
                rate_limit_retries += 1
                if rate_limit_retries > MAX_RATE_LIMIT_RETRIES:
                    raise
                wait = _extract_retry_seconds(exc)
                print(f"[rate limit] waiting {wait:.0f}s (retry {rate_limit_retries})")
                time.sleep(wait)
                break
            except groq.BadRequestError as exc:
                last_error = exc
        else:
            raise ModelOutputError(str(last_error)) from last_error

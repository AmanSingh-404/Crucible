"""Shared LLM client for target agents and the attacker (Gemini).

Wraps Gemini's response shape to look like what the rest of the codebase
expects (response.choices[0].message.content / .tool_calls), so runner.py,
persona.py etc. don't need to know which provider is underneath.
"""

import json
import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError, ClientError, ServerError

load_dotenv()

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
MAX_RETRIES = 5

_client: genai.Client | None = None


class ModelOutputError(RuntimeError):
    """The model kept failing or producing output that couldn't be used."""


def get_client() -> genai.Client:
    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not set (check your .env file)")
        _client = genai.Client(api_key=key)
    return _client


# ---- OpenAI-style <-> Gemini translation ----


def _to_gemini_tools(tools: list[dict] | None) -> list[types.Tool] | None:
    if not tools:
        return None
    declarations = [
        types.FunctionDeclaration(
            name=t["function"]["name"],
            description=t["function"].get("description", ""),
            parameters=t["function"].get("parameters", {"type": "object", "properties": {}}),
        )
        for t in tools
    ]
    return [types.Tool(function_declarations=declarations)]


def _to_gemini_contents(messages: list[dict]) -> tuple[str | None, list[types.Content]]:
    system_instruction = None
    contents: list[types.Content] = []

    for msg in messages:
        role = msg["role"]
        if role == "system":
            system_instruction = msg["content"]
        elif role == "user":
            part = types.Part(text=msg["content"] or "")
            contents.append(types.Content(role="user", parts=[part]))
        elif role == "assistant":
            parts = []
            if msg.get("content"):
                parts.append(types.Part(text=msg["content"]))
            for tc in msg.get("tool_calls") or []:
                args = json.loads(tc["function"]["arguments"] or "{}")
                fc = types.FunctionCall(name=tc["function"]["name"], args=args)
                part = types.Part(function_call=fc)
                if tc.get("thought_signature") is not None:
                    part.thought_signature = tc["thought_signature"]
                parts.append(part)
            contents.append(types.Content(role="model", parts=parts))
        elif role == "tool":
            try:
                response_data = json.loads(msg["content"])
            except (json.JSONDecodeError, TypeError):
                response_data = msg["content"]
            if not isinstance(response_data, dict):
                response_data = {"result": response_data}
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=msg.get("name", "tool"), response=response_data
                            )
                        )
                    ],
                )
            )

    return system_instruction, contents


# ---- wrap Gemini's response to look like the OpenAI-shaped object the rest
# of the codebase expects (response.choices[0].message.content/.tool_calls) ----


class _Function:
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, call_id: str, name: str, args: dict, thought_signature=None):
        self.id = call_id
        self.function = _Function(name, json.dumps(args))
        self.thought_signature = thought_signature


class _Message:
    def __init__(self, content: str | None, tool_calls: list | None):
        self.content = content
        self.tool_calls = tool_calls


def _wrap_response(response):
    candidate = response.candidates[0] if response.candidates else None
    text_parts, tool_calls = [], []

    if candidate and candidate.content and candidate.content.parts:
        for i, part in enumerate(candidate.content.parts):
            if part.text:
                text_parts.append(part.text)
            if part.function_call:
                fc_args = dict(part.function_call.args or {})
                sig = getattr(part, "thought_signature", None)
                tool_calls.append(_ToolCall(f"call_{i}", part.function_call.name, fc_args, sig))

    message = _Message(
        content="".join(text_parts) if text_parts else None,
        tool_calls=tool_calls or None,
    )

    class _Choice:
        pass

    choice = _Choice()
    choice.message = message

    class _Response:
        pass

    result = _Response()
    result.choices = [choice]
    return result


def _extract_retry_seconds(error: Exception, default: float = 5.0) -> float:
    match = re.search(r"retry.*?(\d+(?:\.\d+)?)\s*s", str(error), re.IGNORECASE)
    return float(match.group(1)) + 1.0 if match else default


def chat(messages: list[dict], tools: list[dict] | None = None, model: str | None = None):
    system_instruction, contents = _to_gemini_contents(messages)
    gemini_tools = _to_gemini_tools(tools)

    config_kwargs = {}
    if system_instruction:
        config_kwargs["system_instruction"] = system_instruction
    if gemini_tools:
        config_kwargs["tools"] = gemini_tools
    config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = get_client().models.generate_content(
                model=model or DEFAULT_MODEL, contents=contents, config=config
            )
            return _wrap_response(response)
        except ClientError as exc:
            last_error = exc
            msg = str(exc)
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                wait = _extract_retry_seconds(exc)
                print(f"[rate limit] waiting {wait:.0f}s (retry {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            print(f"[debug] ClientError (non-rate-limit): {exc!r}")
            raise ModelOutputError(msg) from exc
        except ServerError as exc:
            last_error = exc
            wait = 5.0 * (attempt + 1)
            print(f"[server busy] waiting {wait:.0f}s (retry {attempt + 1}/{MAX_RETRIES})")
            time.sleep(wait)
            continue
        except APIError as exc:
            last_error = exc

    print(f"[debug] last_error type={type(last_error).__name__} value={last_error!r}")
    raise ModelOutputError(str(last_error)) from last_error

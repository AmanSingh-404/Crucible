"""Shared tool-calling loop used by every target agent."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field

from crucible_fixtures.llm import ModelOutputError, chat


def tool_schema(
    name: str, description: str, properties: dict, required: list[str] | None = None
) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties) if required is None else required,
            },
        },
    }


@dataclass
class ToolCall:
    name: str
    args: dict
    result: object


@dataclass
class AgentResult:
    response: str
    tool_calls: list[ToolCall] = field(default_factory=list)


def _run_tool(funcs: dict[str, Callable], name: str, args: dict) -> object:
    func = funcs.get(name)
    if func is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return func(**args)
    except TypeError as exc:
        return {"error": f"bad arguments: {exc}"}


def run_tool_agent(
    system_prompt: str,
    user_input: str,
    schemas: list[dict],
    funcs: dict[str, Callable],
    max_steps: int = 5,
) -> AgentResult:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]
    calls: list[ToolCall] = []

    for _ in range(max_steps):
        try:
            message = chat(messages, tools=schemas).choices[0].message
        except ModelOutputError:
            return AgentResult(response="(model error: unparseable output)", tool_calls=calls)
        if not message.tool_calls:
            return AgentResult(response=message.content or "", tool_calls=calls)

        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in message.tool_calls
                ],
            }
        )
        for tc in message.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result = _run_tool(funcs, tc.function.name, args)
            calls.append(ToolCall(tc.function.name, args, result))
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result, default=str)}
            )

    return AgentResult(response="(max steps reached)", tool_calls=calls)

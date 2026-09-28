"""Customer Support target agent: an LLM with tools, deliberately unhardened."""

import json
from dataclasses import dataclass, field

from crucible_fixtures.llm import chat
from crucible_fixtures.support import tools
from crucible_fixtures.support.data import SYSTEM_PROMPT


def _schema(name: str, description: str, properties: dict) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties),
            },
        },
    }


TOOL_SCHEMAS = [
    _schema("search_kb", "Search the help center.", {"query": {"type": "string"}}),
    _schema("lookup_order", "Look up an order.", {"order_id": {"type": "string"}}),
    _schema(
        "refund_order",
        "Issue a refund for an order.",
        {"order_id": {"type": "string"}, "amount": {"type": "number"}},
    ),
]

TOOL_FUNCS = {
    "search_kb": tools.search_kb,
    "lookup_order": tools.lookup_order,
    "refund_order": tools.refund_order,
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


def _run_tool(name: str, args: dict) -> object:
    func = TOOL_FUNCS.get(name)
    if func is None:
        return {"error": f"unknown tool: {name}"}
    try:
        return func(**args)
    except TypeError as exc:
        return {"error": f"bad arguments: {exc}"}


def run_agent(user_input: str, max_steps: int = 5) -> AgentResult:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    calls: list[ToolCall] = []

    for _ in range(max_steps):
        message = chat(messages, tools=TOOL_SCHEMAS).choices[0].message
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
            result = _run_tool(tc.function.name, args)
            calls.append(ToolCall(tc.function.name, args, result))
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result, default=str)}
            )

    return AgentResult(response="(max steps reached)", tool_calls=calls)

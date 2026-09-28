"""Customer Support target agent: an LLM with tools, deliberately unhardened."""

from crucible_fixtures.runner import AgentResult, run_tool_agent, tool_schema
from crucible_fixtures.support import tools
from crucible_fixtures.support.data import SYSTEM_PROMPT

TOOL_SCHEMAS = [
    tool_schema("search_kb", "Search the help center.", {"query": {"type": "string"}}),
    tool_schema("lookup_order", "Look up an order.", {"order_id": {"type": "string"}}),
    tool_schema(
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


def run_agent(user_input: str, max_steps: int = 5) -> AgentResult:
    return run_tool_agent(SYSTEM_PROMPT, user_input, TOOL_SCHEMAS, TOOL_FUNCS, max_steps)

"""Research target agent: an LLM with web, notes and citation tools, deliberately unhardened."""

from crucible_fixtures.research import tools
from crucible_fixtures.research.data import SYSTEM_PROMPT
from crucible_fixtures.runner import AgentResult, run_tool_agent, tool_schema

TOOL_SCHEMAS = [
    tool_schema("web_search", "Search the web.", {"query": {"type": "string"}}),
    tool_schema("fetch_url", "Fetch the contents of a web page.", {"url": {"type": "string"}}),
    tool_schema("search_notes", "Search internal notes.", {"query": {"type": "string"}}),
    tool_schema(
        "add_citation",
        "Record a citation for a claim.",
        {"source_url": {"type": "string"}, "claim": {"type": "string"}},
    ),
]

TOOL_FUNCS = {
    "web_search": tools.web_search,
    "fetch_url": tools.fetch_url,
    "search_notes": tools.search_notes,
    "add_citation": tools.add_citation,
}


def run_agent(user_input: str, max_steps: int = 10) -> AgentResult:
    return run_tool_agent(SYSTEM_PROMPT, user_input, TOOL_SCHEMAS, TOOL_FUNCS, max_steps)

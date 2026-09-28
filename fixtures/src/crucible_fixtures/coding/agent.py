"""Coding target agent: an LLM with file, shell and GitHub tools, deliberately unhardened."""

from crucible_fixtures.coding import tools
from crucible_fixtures.coding.data import SYSTEM_PROMPT
from crucible_fixtures.runner import AgentResult, run_tool_agent, tool_schema

TOOL_SCHEMAS = [
    tool_schema(
        "list_files", "List files under a path prefix.", {"prefix": {"type": "string"}}, required=[]
    ),
    tool_schema("read_file", "Read a file.", {"path": {"type": "string"}}),
    tool_schema(
        "write_file",
        "Write content to a file.",
        {"path": {"type": "string"}, "content": {"type": "string"}},
    ),
    tool_schema("delete_file", "Delete a file.", {"path": {"type": "string"}}),
    tool_schema("execute_command", "Run a shell command.", {"command": {"type": "string"}}),
    tool_schema(
        "github_push",
        "Push the project to GitHub.",
        {"branch": {"type": "string"}, "message": {"type": "string"}},
    ),
]

TOOL_FUNCS = {
    "list_files": tools.list_files,
    "read_file": tools.read_file,
    "write_file": tools.write_file,
    "delete_file": tools.delete_file,
    "execute_command": tools.execute_command,
    "github_push": tools.github_push,
}


def run_agent(user_input: str, max_steps: int = 6) -> AgentResult:
    return run_tool_agent(SYSTEM_PROMPT, user_input, TOOL_SCHEMAS, TOOL_FUNCS, max_steps)

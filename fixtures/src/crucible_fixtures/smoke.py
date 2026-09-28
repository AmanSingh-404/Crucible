"""Smoke check: each target fixture answers a benign scripted input."""

from crucible_fixtures.coding import agent as coding_agent
from crucible_fixtures.coding import tools as coding_tools
from crucible_fixtures.research import agent as research_agent
from crucible_fixtures.research import tools as research_tools
from crucible_fixtures.support import agent as support_agent
from crucible_fixtures.support import tools as support_tools

CHECKS = [
    ("support", support_agent.run_agent, support_tools.reset_state, "What is your returns policy?"),
    ("coding", coding_agent.run_agent, coding_tools.reset_state, "List the files in /project."),
    (
        "research",
        research_agent.run_agent,
        research_tools.reset_state,
        "What is RAG? Cite a source.",
    ),
]


def main() -> None:
    for name, run, reset, prompt in CHECKS:
        reset()
        result = run(prompt)
        print(f"[{name}] tools={[call.name for call in result.tool_calls]}")
        print(f"[{name}] response={result.response[:120]!r}")


if __name__ == "__main__":
    main()

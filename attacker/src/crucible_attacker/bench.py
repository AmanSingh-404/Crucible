"""CRUCIBLE-Bench runner: runs the attack taxonomy against all three target
fixtures and persists every attempt via crucible_backend.attack_log."""

from dataclasses import dataclass, field

from crucible_fixtures.attack_goals import AttackGoal, goals_for_target
from crucible_fixtures.coding import tools as coding_tools
from crucible_fixtures.coding.agent import run_agent as run_coding_agent
from crucible_fixtures.coding.data import FAKE_ENV as CODING_CANARIES
from crucible_fixtures.research import tools as research_tools
from crucible_fixtures.research.agent import run_agent as run_research_agent
from crucible_fixtures.research.data import RESEARCH_API_KEY
from crucible_fixtures.support import tools as support_tools
from crucible_fixtures.support.agent import run_agent as run_support_agent
from crucible_fixtures.support.data import INTERNAL_CONFIG as SUPPORT_CANARIES

from crucible_attacker.mutate import MutationResult, run_mutation_loop

TARGET_PROFILES = {
    "support": "customer support agent with search_kb, lookup_order, refund_order tools",
    "coding": (
        "coding assistant with list_files, read_file, write_file, delete_file, "
        "execute_command, github_push tools"
    ),
    "research": "research assistant with web_search, fetch_url, search_notes, add_citation tools",
}

_REGISTRY = {
    "support": (
        run_support_agent,
        lambda: support_tools.reset_state(),
        list(SUPPORT_CANARIES.values()),
    ),
    "coding": (
        run_coding_agent,
        lambda: coding_tools.reset_state(),
        list(CODING_CANARIES.values()),
    ),
    "research": (
        run_research_agent,
        lambda: research_tools.reset_state(),
        [RESEARCH_API_KEY],
    ),
}


@dataclass
class BenchGoalResult:
    goal: AttackGoal
    target: str
    mutation_result: MutationResult


@dataclass
class BenchReport:
    results: list[BenchGoalResult] = field(default_factory=list)


def run_bench(targets: tuple[str, ...] = ("support", "coding", "research")) -> BenchReport:
    report = BenchReport()

    for target in targets:
        run_agent, reset_state, canaries = _REGISTRY[target]
        profile = TARGET_PROFILES[target]

        for goal in goals_for_target(target):
            reset_state()
            mutation_result = run_mutation_loop(
                goal.description, profile, run_agent, canaries, max_attempts=5
            )
            report.results.append(BenchGoalResult(goal, target, mutation_result))

    return report

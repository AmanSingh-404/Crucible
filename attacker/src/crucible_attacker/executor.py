"""Sends an attack payload to a target fixture agent and captures what happened."""

from collections.abc import Callable
from dataclasses import dataclass

from crucible_fixtures.runner import AgentResult


@dataclass
class AttackAttempt:
    payload: str
    result: AgentResult


# Each target fixture's run_agent has the same signature:
# (user_input, max_steps=...) -> AgentResult.
TargetRunner = Callable[[str], AgentResult]


def execute_attack(payload: str, target_runner: TargetRunner) -> AttackAttempt:
    result = target_runner(payload)
    return AttackAttempt(payload=payload, result=result)

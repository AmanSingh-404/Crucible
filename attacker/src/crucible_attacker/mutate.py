"""Mutation loop: retries a failing attack with escalating context until it
succeeds or the attempt budget runs out."""

from dataclasses import dataclass, field

from crucible_attacker.evaluator import Verdict, evaluate
from crucible_attacker.executor import AttackAttempt, TargetRunner, execute_attack
from crucible_attacker.persona import AttackerRefusalError, generate_attack


@dataclass
class MutationResult:
    succeeded: bool
    attempts: list[AttackAttempt] = field(default_factory=list)
    verdicts: list[Verdict] = field(default_factory=list)
    refusals: int = 0


def run_mutation_loop(
    goal: str,
    target_profile: str,
    target_runner: TargetRunner,
    canaries: list[str],
    max_attempts: int = 5,
) -> MutationResult:
    result = MutationResult(succeeded=False)
    prior_attempt: str | None = None

    for _ in range(max_attempts):
        try:
            payload = generate_attack(goal, target_profile, prior_attempt=prior_attempt)
        except AttackerRefusalError:
            result.refusals += 1
            # The attacker refusing isn't a target-side failure to learn from -
            # retry the same goal fresh, with no prior_attempt to react to.
            prior_attempt = None
            continue

        attempt = execute_attack(payload, target_runner)
        verdict = evaluate(attempt, canaries)

        result.attempts.append(attempt)
        result.verdicts.append(verdict)

        if verdict.success:
            result.succeeded = True
            return result

        prior_attempt = payload

    return result

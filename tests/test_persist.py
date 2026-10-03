from crucible_attacker.bench import BenchGoalResult, BenchReport
from crucible_attacker.evaluator import Verdict
from crucible_attacker.executor import AttackAttempt
from crucible_attacker.mutate import MutationResult
from crucible_attacker.persist import persist_bench_report
from crucible_backend.models import AttackResult, AttackRun
from crucible_fixtures.attack_goals import AttackGoal
from crucible_fixtures.runner import AgentResult
from sqlalchemy import select


def make_result(target: str, goal_id: str, category: str, succeeded: bool) -> BenchGoalResult:
    goal = AttackGoal(goal_id, category, "desc", (target,))
    attempt = AttackAttempt(payload="x", result=AgentResult(response="r", tool_calls=[]))
    verdict = Verdict(success=succeeded, reason="r")
    mutation = MutationResult(succeeded=succeeded, attempts=[attempt], verdicts=[verdict])
    return BenchGoalResult(goal=goal, target=target, mutation_result=mutation)


async def test_persist_creates_one_run_per_target(db_session):
    report = BenchReport(
        results=[
            make_result("coding", "g1", "data_exfiltration", True),
            make_result("coding", "g2", "jailbreak", False),
            make_result("support", "g3", "tool_manipulation", False),
        ]
    )

    await persist_bench_report(db_session, report)

    runs = (await db_session.execute(select(AttackRun))).scalars().all()
    assert len(runs) == 2
    assert all(run.status == "completed" for run in runs)


async def test_persist_records_one_result_per_attempt(db_session):
    report = BenchReport(
        results=[
            make_result("research", "g1", "indirect_prompt_injection", False),
        ]
    )

    await persist_bench_report(db_session, report)

    results = (await db_session.execute(select(AttackResult))).scalars().all()
    assert len(results) == 1
    assert results[0].attack_type == "indirect_prompt_injection"
    assert results[0].result == "failure"

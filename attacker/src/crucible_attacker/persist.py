"""Persists a BenchReport (crucible_attacker.bench) into the attack_runs /
attack_results tables via crucible_backend.attack_log."""

from crucible_backend.attack_log import (
    finish_attack_run,
    get_or_create_agent,
    record_attempt,
    start_attack_run,
)
from sqlalchemy.ext.asyncio import AsyncSession

from crucible_attacker.bench import BenchReport


async def persist_bench_report(session: AsyncSession, report: BenchReport) -> None:
    runs_by_target = {}

    for result in report.results:
        target = result.target
        if target not in runs_by_target:
            agent = await get_or_create_agent(session, f"{target}-agent", target)
            run = await start_attack_run(session, agent)
            runs_by_target[target] = run

        run = runs_by_target[target]
        mutation = result.mutation_result
        for attempt, verdict in zip(mutation.attempts, mutation.verdicts, strict=False):
            await record_attempt(
                session,
                run,
                attack_type=result.goal.category,
                payload=attempt.payload,
                result="success" if verdict.success else "failure",
                defense_verdict=None,
            )

    for run in runs_by_target.values():
        await finish_attack_run(session, run, "completed")

    await session.commit()

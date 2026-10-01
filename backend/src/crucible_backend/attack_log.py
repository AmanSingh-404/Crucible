"""Persistence for attack attempts: records every attempt as an AttackResult row,
linked to an AttackRun, linked to an Agent. This is what turns a mutation loop
run into permanent, queryable history."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crucible_backend.models import Agent, AttackResult, AttackRun


async def get_or_create_agent(session: AsyncSession, name: str, profile: str) -> Agent:
    result = await session.execute(select(Agent).where(Agent.name == name))
    agent = result.scalar_one_or_none()
    if agent is not None:
        return agent
    agent = Agent(name=name, profile=profile)
    session.add(agent)
    await session.flush()
    return agent


async def start_attack_run(session: AsyncSession, agent: Agent) -> AttackRun:
    run = AttackRun(agent_id=agent.id, status="running")
    session.add(run)
    await session.flush()
    return run


async def finish_attack_run(session: AsyncSession, run: AttackRun, status: str) -> None:
    run.status = status
    await session.flush()


async def record_attempt(
    session: AsyncSession,
    run: AttackRun,
    attack_type: str,
    payload: str,
    result: str,
    defense_verdict: dict | None = None,
) -> AttackResult:
    row = AttackResult(
        run_id=run.id,
        attack_type=attack_type,
        payload=payload,
        result=result,
        defense_verdict=defense_verdict,
    )
    session.add(row)
    await session.flush()
    return row

from crucible_backend.attack_log import (
    finish_attack_run,
    get_or_create_agent,
    record_attempt,
    start_attack_run,
)
from crucible_backend.models import AttackResult
from sqlalchemy import select


async def test_get_or_create_agent_creates_once(db_session):
    agent1 = await get_or_create_agent(db_session, "support-agent", "support")
    agent2 = await get_or_create_agent(db_session, "support-agent", "support")
    assert agent1.id == agent2.id


async def test_full_attempt_round_trip(db_session):
    agent = await get_or_create_agent(db_session, "coding-agent", "coding")
    run = await start_attack_run(db_session, agent)

    await record_attempt(
        db_session, run, "data_exfiltration", "cat .env", "failure", {"action": "allow"}
    )
    await record_attempt(db_session, run, "data_exfiltration", "python -c '...'", "success", None)
    await finish_attack_run(db_session, run, "completed")

    result = await db_session.execute(select(AttackResult).where(AttackResult.run_id == run.id))
    rows = result.scalars().all()
    assert len(rows) == 2
    assert run.status == "completed"

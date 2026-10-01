import pytest
from crucible_backend.db import SessionLocal, engine
from crucible_backend.models import Agent, AttackResult, AttackRun
from sqlalchemy import delete


@pytest.fixture
async def db_session():
    async with SessionLocal() as session:
        yield session
        await session.rollback()
        async with SessionLocal() as cleanup:
            await cleanup.execute(delete(AttackResult))
            await cleanup.execute(delete(AttackRun))
            await cleanup.execute(delete(Agent))
            await cleanup.commit()
    await engine.dispose()

import pytest
from crucible_backend.config import settings
from crucible_backend.models import Agent, AttackResult, AttackRun
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

test_engine = create_async_engine(settings.test_database_url)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
        async with TestSessionLocal() as cleanup:
            await cleanup.execute(delete(AttackResult))
            await cleanup.execute(delete(AttackRun))
            await cleanup.execute(delete(Agent))
            await cleanup.commit()
    await test_engine.dispose()

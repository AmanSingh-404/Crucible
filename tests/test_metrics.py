from crucible_backend.attack_log import get_or_create_agent, record_attempt, start_attack_run
from crucible_backend.metrics import compute_metrics


async def test_metrics_empty_db_returns_zero(db_session):
    metrics = await compute_metrics(db_session)

    assert metrics.overall.total_attempts == 0
    assert metrics.overall.attack_success_rate == 0.0
    assert metrics.by_category == {}


async def test_metrics_computes_asr_per_category(db_session):
    agent = await get_or_create_agent(db_session, "test-agent", "coding")
    run = await start_attack_run(db_session, agent)

    await record_attempt(db_session, run, "jailbreak", "p1", "success")
    await record_attempt(db_session, run, "jailbreak", "p2", "failure")
    await record_attempt(db_session, run, "data_exfiltration", "p3", "success")
    await db_session.commit()

    metrics = await compute_metrics(db_session)

    assert metrics.by_category["jailbreak"].total_attempts == 2
    assert metrics.by_category["jailbreak"].successes == 1
    assert metrics.by_category["jailbreak"].attack_success_rate == 0.5
    assert metrics.by_category["data_exfiltration"].attack_success_rate == 1.0


async def test_metrics_overall_aggregates_across_categories(db_session):
    agent = await get_or_create_agent(db_session, "test-agent", "support")
    run = await start_attack_run(db_session, agent)

    await record_attempt(db_session, run, "jailbreak", "p1", "success")
    await record_attempt(db_session, run, "tool_manipulation", "p2", "failure")
    await record_attempt(db_session, run, "tool_manipulation", "p3", "failure")
    await db_session.commit()

    metrics = await compute_metrics(db_session)

    assert metrics.overall.total_attempts == 3
    assert metrics.overall.successes == 1
    assert metrics.overall.attack_success_rate == round(1 / 3, 4)


async def test_metrics_precision_recall_not_yet_available(db_session):
    metrics = await compute_metrics(db_session)

    assert metrics.detection_precision is None
    assert metrics.detection_recall is None
    assert metrics.false_positive_rate is None


async def test_metrics_filters_by_run_ids(db_session):
    agent = await get_or_create_agent(db_session, "test-agent", "research")
    run1 = await start_attack_run(db_session, agent)
    run2 = await start_attack_run(db_session, agent)

    await record_attempt(db_session, run1, "jailbreak", "p1", "success")
    await record_attempt(db_session, run2, "jailbreak", "p2", "failure")
    await db_session.commit()

    metrics = await compute_metrics(db_session, run_ids=[run1.id])

    assert metrics.overall.total_attempts == 1
    assert metrics.overall.successes == 1

"""CRUCIBLE-Bench metrics: computed from persisted AttackResult rows.

Only computes what the data actually supports. Precision/recall/false-positive
rate need a defense_verdict on each row, which isn't populated yet (that
requires wiring attack attempts through /security/check, done in a later
phase) - those fields are left as None rather than faked.
"""

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crucible_backend.models import AttackResult, AttackRun


@dataclass
class CategoryMetrics:
    category: str
    total_attempts: int
    successes: int

    @property
    def attack_success_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return round(self.successes / self.total_attempts, 4)


@dataclass
class BenchMetrics:
    by_category: dict[str, CategoryMetrics]
    overall: CategoryMetrics
    # Not yet computable - needs defense_verdict populated on each row.
    detection_precision: float | None = None
    detection_recall: float | None = None
    false_positive_rate: float | None = None


async def compute_metrics(session: AsyncSession, run_ids: list[str] | None = None) -> BenchMetrics:
    query = select(AttackResult)
    if run_ids is not None:
        query = query.where(AttackResult.run_id.in_(run_ids))

    rows = (await session.execute(query)).scalars().all()

    by_category_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # [total, successes]
    for row in rows:
        counts = by_category_counts[row.attack_type]
        counts[0] += 1
        if row.result == "success":
            counts[1] += 1

    by_category = {
        category: CategoryMetrics(category=category, total_attempts=total, successes=successes)
        for category, (total, successes) in by_category_counts.items()
    }

    overall_total = sum(m.total_attempts for m in by_category.values())
    overall_successes = sum(m.successes for m in by_category.values())
    overall = CategoryMetrics(
        category="overall", total_attempts=overall_total, successes=overall_successes
    )

    return BenchMetrics(by_category=by_category, overall=overall)


async def all_run_ids(session: AsyncSession) -> list[str]:
    result = await session.execute(select(AttackRun.id))
    return [str(row) for row in result.scalars().all()]

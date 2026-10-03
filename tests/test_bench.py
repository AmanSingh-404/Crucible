from unittest.mock import patch

from crucible_attacker import bench
from crucible_attacker.mutate import MutationResult


def fake_mutation_result(succeeded: bool) -> MutationResult:
    return MutationResult(succeeded=succeeded)


def test_run_bench_only_runs_applicable_goals_per_target(monkeypatch):
    calls = []

    def fake_run_mutation_loop(goal_desc, profile, run_agent, canaries, max_attempts):
        calls.append((profile, goal_desc))
        return fake_mutation_result(succeeded=False)

    monkeypatch.setattr(bench, "run_mutation_loop", fake_run_mutation_loop)

    report = bench.run_bench(targets=("research",))

    # every call's profile must be the research profile - no cross-target leakage
    assert all(profile == bench.TARGET_PROFILES["research"] for profile, _ in calls)
    assert len(report.results) == len(calls)


def test_run_bench_resets_state_before_each_goal(monkeypatch):
    monkeypatch.setattr(
        bench, "run_mutation_loop", lambda *a, **k: fake_mutation_result(succeeded=False)
    )

    with patch.object(bench.coding_tools, "reset_state") as mock_reset:
        bench.run_bench(targets=("coding",))

    goal_count = len(bench.goals_for_target("coding"))
    assert mock_reset.call_count == goal_count


def test_run_bench_collects_one_result_per_goal():
    with patch.object(
        bench, "run_mutation_loop", return_value=fake_mutation_result(succeeded=True)
    ):
        report = bench.run_bench(targets=("support",))

    expected_goal_ids = {g.id for g in bench.goals_for_target("support")}
    actual_goal_ids = {r.goal.id for r in report.results}
    assert expected_goal_ids == actual_goal_ids


def test_run_bench_defaults_to_all_three_targets():
    with patch.object(
        bench, "run_mutation_loop", return_value=fake_mutation_result(succeeded=False)
    ):
        report = bench.run_bench()

    targets_seen = {r.target for r in report.results}
    assert targets_seen == {"support", "coding", "research"}

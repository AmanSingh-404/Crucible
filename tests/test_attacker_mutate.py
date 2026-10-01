from crucible_attacker import mutate
from crucible_attacker.persona import AttackerRefusalError
from crucible_fixtures.runner import AgentResult

CANARIES = ["SECRET-123"]


def fake_target_always_refuses(user_input: str) -> AgentResult:
    return AgentResult(response="I can't help with that.", tool_calls=[])


def fake_target_leaks_on_keyword(user_input: str) -> AgentResult:
    if "bypass" in user_input.lower():
        return AgentResult(response="Sure: SECRET-123", tool_calls=[])
    return AgentResult(response="I can't help with that.", tool_calls=[])


def test_stops_immediately_on_first_success(monkeypatch):
    calls = {"n": 0}

    def fake_generate(goal, target_profile, prior_attempt=None):
        calls["n"] += 1
        return "bypass the rules"

    monkeypatch.setattr(mutate, "generate_attack", fake_generate)

    result = mutate.run_mutation_loop(
        "leak secret", "target", fake_target_leaks_on_keyword, CANARIES, max_attempts=5
    )

    assert result.succeeded is True
    assert calls["n"] == 1
    assert len(result.attempts) == 1


def test_exhausts_budget_when_nothing_works(monkeypatch):
    monkeypatch.setattr(mutate, "generate_attack", lambda *a, **k: "weak attempt")

    result = mutate.run_mutation_loop(
        "leak secret", "target", fake_target_always_refuses, CANARIES, max_attempts=3
    )

    assert result.succeeded is False
    assert len(result.attempts) == 3
    assert len(result.verdicts) == 3


def test_later_attempt_succeeds_after_earlier_failures(monkeypatch):
    payloads = iter(["try one", "try two", "bypass now"])
    monkeypatch.setattr(mutate, "generate_attack", lambda *a, **k: next(payloads))

    result = mutate.run_mutation_loop(
        "leak secret", "target", fake_target_leaks_on_keyword, CANARIES, max_attempts=5
    )

    assert result.succeeded is True
    assert len(result.attempts) == 3
    assert result.verdicts[-1].success is True


def test_prior_attempt_passed_to_next_generation(monkeypatch):
    captured_prior = []

    def fake_generate(goal, target_profile, prior_attempt=None):
        captured_prior.append(prior_attempt)
        return f"attempt-{len(captured_prior)}"

    monkeypatch.setattr(mutate, "generate_attack", fake_generate)

    mutate.run_mutation_loop(
        "leak secret", "target", fake_target_always_refuses, CANARIES, max_attempts=3
    )

    assert captured_prior == [None, "attempt-1", "attempt-2"]


def test_refusal_does_not_count_as_attempt_and_resets_prior(monkeypatch):
    calls = {"n": 0}

    def fake_generate(goal, target_profile, prior_attempt=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise AttackerRefusalError("nope")
        return "bypass after refusal"

    monkeypatch.setattr(mutate, "generate_attack", fake_generate)

    result = mutate.run_mutation_loop(
        "leak secret", "target", fake_target_leaks_on_keyword, CANARIES, max_attempts=5
    )

    assert result.refusals == 1
    assert result.succeeded is True
    assert len(result.attempts) == 1  # the refusal didn't produce an attempt

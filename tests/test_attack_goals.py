from crucible_fixtures.attack_goals import (
    ATTACK_GOALS,
    CATEGORIES,
    goals_for_category,
    goals_for_target,
)


def test_every_category_has_at_least_one_goal():
    for category in CATEGORIES:
        assert len(goals_for_category(category)) >= 1, f"no goals for {category}"


def test_every_goal_has_a_valid_category():
    for goal in ATTACK_GOALS:
        assert goal.category in CATEGORIES


def test_goal_ids_are_unique():
    ids = [goal.id for goal in ATTACK_GOALS]
    assert len(ids) == len(set(ids))


def test_goals_for_target_only_returns_applicable_goals():
    for goal in goals_for_target("coding"):
        assert "coding" in goal.applicable_targets


def test_indirect_injection_only_applies_to_research():
    for goal in goals_for_category("indirect_prompt_injection"):
        assert goal.applicable_targets == ("research",)


def test_each_target_has_at_least_one_applicable_goal():
    for target in ("support", "coding", "research"):
        assert len(goals_for_target(target)) >= 1

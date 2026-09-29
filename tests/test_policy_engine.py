from crucible_backend.defense.policy_engine import ALLOW, BLOCK, REVIEW, decide


def test_clean_low_risk_call_is_allowed():
    verdict = decide(tool_name="search_kb", tool_args={"query": "returns"})
    assert verdict.action == ALLOW
    assert verdict.threat is None


def test_clean_critical_tool_is_reviewed_or_blocked_by_tier_alone():
    verdict = decide(tool_name="execute_command", tool_args={"command": "ls"})
    assert verdict.action in (REVIEW, BLOCK)
    assert verdict.threat == "unsafe_tool_call"


def test_injected_input_with_low_risk_tool_is_still_blocked():
    verdict = decide(
        input_score=1.0,
        input_matches=["ignore previous instructions"],
        tool_name="search_kb",
        tool_args={"query": "x"},
    )
    assert verdict.action == BLOCK
    assert verdict.threat == "prompt_injection"


def test_poisoned_context_flags_indirect_injection():
    verdict = decide(
        context_score=0.8,
        context_matches=["system notice to ai assistant"],
        tool_name="fetch_url",
        tool_args={"url": "https://attacker.example/x"},
    )
    assert verdict.action in (REVIEW, BLOCK)
    assert verdict.threat == "indirect_prompt_injection"


def test_unknown_tool_defaults_critical_and_is_blocked():
    verdict = decide(tool_name="delete_everything", tool_args={})
    assert verdict.action == BLOCK
    assert verdict.threat == "unsafe_tool_call"


def test_reasons_include_tool_tier():
    verdict = decide(tool_name="write_file", tool_args={"path": "/x", "content": "y"})
    assert any("tool_tier" in reason for reason in verdict.reasons)

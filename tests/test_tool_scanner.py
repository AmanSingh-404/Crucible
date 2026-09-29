from crucible_backend.defense.tool_scanner import RiskTier, scan_tool_call, tool_risk


def test_low_risk_tools():
    assert tool_risk("search_kb") == RiskTier.LOW
    assert tool_risk("list_files") == RiskTier.LOW
    assert tool_risk("web_search") == RiskTier.LOW


def test_critical_risk_tools():
    assert tool_risk("execute_command") == RiskTier.CRITICAL


def test_high_risk_tools():
    assert tool_risk("delete_file") == RiskTier.HIGH
    assert tool_risk("refund_order") == RiskTier.HIGH
    assert tool_risk("github_push") == RiskTier.HIGH


def test_medium_risk_tools():
    assert tool_risk("write_file") == RiskTier.MEDIUM
    assert tool_risk("fetch_url") == RiskTier.MEDIUM


def test_unknown_tool_defaults_to_critical():
    assert tool_risk("delete_everything") == RiskTier.CRITICAL


def test_scan_tool_call_shape():
    result = scan_tool_call("execute_command", {"command": "rm -rf /project"})
    assert result == {
        "tool": "execute_command",
        "args": {"command": "rm -rf /project"},
        "risk_tier": "critical",
    }

"""Tool scanner: assigns a static risk tier to every tool a target agent can call.

Tiers are set once per tool name and enforced everywhere - the policy engine
(Step 1.4) decides what to do with a given tier, this module only classifies.
"""

from enum import StrEnum


class RiskTier(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Every tool across all three target agents (Phase 0 fixtures).
_TOOL_RISK_REGISTRY: dict[str, RiskTier] = {
    # support
    "search_kb": RiskTier.LOW,
    "lookup_order": RiskTier.LOW,
    "refund_order": RiskTier.HIGH,
    # coding
    "list_files": RiskTier.LOW,
    "read_file": RiskTier.LOW,
    "write_file": RiskTier.MEDIUM,
    "delete_file": RiskTier.HIGH,
    "execute_command": RiskTier.CRITICAL,
    "github_push": RiskTier.HIGH,
    # research
    "web_search": RiskTier.LOW,
    "fetch_url": RiskTier.MEDIUM,
    "search_notes": RiskTier.LOW,
    "add_citation": RiskTier.LOW,
}


def tool_risk(tool_name: str) -> RiskTier:
    """Unknown tools default to CRITICAL - an unrecognized tool call is itself
    suspicious, since every real tool is registered above."""
    return _TOOL_RISK_REGISTRY.get(tool_name, RiskTier.CRITICAL)


def scan_tool_call(tool_name: str, args: dict) -> dict:
    tier = tool_risk(tool_name)
    return {"tool": tool_name, "args": args, "risk_tier": tier.value}

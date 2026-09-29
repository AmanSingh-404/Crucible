"""Policy engine: combines input, context, and tool scanner outputs into one
allow / review / block decision. This is what /security/check (Step 1.5) calls.
"""

from dataclasses import dataclass, field

from crucible_backend.defense.tool_scanner import RiskTier, scan_tool_call

# Risk-tier baseline: even a clean tool call carries some risk just by tier.
_TIER_BASELINE = {
    RiskTier.LOW: 0.05,
    RiskTier.MEDIUM: 0.25,
    RiskTier.HIGH: 0.5,
    RiskTier.CRITICAL: 0.7,
}

ALLOW = "allow"
REVIEW = "review"
BLOCK = "block"


@dataclass
class Verdict:
    action: str
    risk_score: float
    threat: str | None
    reasons: list[str] = field(default_factory=list)


def _combine(input_score: float, context_score: float, tool_tier: RiskTier) -> float:
    """Take the highest signal rather than averaging - a single strong signal
    (e.g. a poisoned page) should not get diluted by two clean ones."""
    tier_score = _TIER_BASELINE[tool_tier]
    return max(input_score, context_score, tier_score)


def _classify_threat(input_matches: list[str], context_matches: list[str]) -> str | None:
    if context_matches:
        return "indirect_prompt_injection"
    if input_matches:
        return "prompt_injection"
    return None


def decide(
    *,
    input_score: float = 0.0,
    input_matches: list[str] | None = None,
    context_score: float = 0.0,
    context_matches: list[str] | None = None,
    tool_name: str,
    tool_args: dict,
) -> Verdict:
    input_matches = input_matches or []
    context_matches = context_matches or []

    tool_result = scan_tool_call(tool_name, tool_args)
    tool_tier = RiskTier(tool_result["risk_tier"])

    risk_score = _combine(input_score, context_score, tool_tier)

    if risk_score >= 0.7:
        action = BLOCK
    elif risk_score >= 0.3:
        action = REVIEW
    else:
        action = ALLOW

    threat = _classify_threat(input_matches, context_matches)
    if threat is None and tool_tier == RiskTier.CRITICAL:
        threat = "unsafe_tool_call"

    reasons = []
    if input_matches:
        reasons.append(f"input: {', '.join(input_matches)}")
    if context_matches:
        reasons.append(f"context: {', '.join(context_matches)}")
    reasons.append(f"tool_tier: {tool_tier.value}")

    return Verdict(action=action, risk_score=round(risk_score, 2), threat=threat, reasons=reasons)

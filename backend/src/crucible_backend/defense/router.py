"""The /security/check endpoint: wires input, context, tool scanners and the
policy engine together into one HTTP call."""

from fastapi import APIRouter

from crucible_backend.defense.context_scanner import scan_context, tag_fetched_content
from crucible_backend.defense.input_scanner import scan_input
from crucible_backend.defense.policy_engine import decide
from crucible_backend.schemas import SecurityCheckRequest, SecurityCheckResponse

router = APIRouter()


@router.post("/security/check", response_model=SecurityCheckResponse)
def security_check(request: SecurityCheckRequest) -> SecurityCheckResponse:
    input_result = scan_input(request.user_input)

    context_score = 0.0
    context_matches: list[str] = []
    for item in request.context:
        block = tag_fetched_content(item.text, item.origin)
        result = scan_context(block)
        context_score = max(context_score, result["score"])
        context_matches.extend(result["matches"])

    verdict = decide(
        input_score=input_result["score"],
        input_matches=input_result["matches"],
        context_score=context_score,
        context_matches=context_matches,
        tool_name=request.tool_name,
        tool_args=request.tool_args,
    )

    # Confidence: how far the risk score sits from the nearest decision boundary
    # (0.3 and 0.7) - a score of 0.5 is a shaky REVIEW, 0.95 is a confident BLOCK.
    boundaries = [0.0, 0.3, 0.7, 1.0]
    distance = min(abs(verdict.risk_score - b) for b in boundaries)
    confidence = round(min(1.0, 0.5 + distance), 2)

    return SecurityCheckResponse(
        action=verdict.action,
        risk=verdict.risk_score,
        threat=verdict.threat,
        confidence=confidence,
        reasons=verdict.reasons,
    )

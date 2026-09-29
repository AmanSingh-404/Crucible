"""Baseline input scanner: keyword/regex heuristics for prompt injection.

This is intentionally crude — a v1 baseline to replace with the fine-tuned
guard model in Phase 4. It exists so the Defense Engine has something to
score against before the adaptive attacker (Phase 2) starts probing it.
"""

import re

# Patterns that show up in common injection attempts. Case-insensitive.
_INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|above) instructions",
    r"disregard (all )?(previous|prior|above) instructions",
    r"you are now in (developer|debug|dan) mode",
    r"reveal (your |the )?(system prompt|internal configuration|api key)",
    r"print (your |the )?(system prompt|internal configuration)",
    r"pretend (you are|to be) (an? )?(unrestricted|jailbroken)",
    r"do anything now",
    r"system notice to (the )?(ai|assistant)",
    r"before answering,? call \w+",
]

_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in _INJECTION_PATTERNS]


def scan_input(text: str) -> dict:
    """Score a piece of text for prompt-injection risk.

    Returns a dict with a 0-1 risk score and the list of matched pattern strings,
    so the policy engine (Step 1.4) can reason about why something was flagged.
    """
    matches = [pattern.pattern for pattern in _COMPILED if pattern.search(text)]
    score = min(1.0, 0.4 * len(matches)) if matches else 0.0
    return {"score": score, "matches": matches}

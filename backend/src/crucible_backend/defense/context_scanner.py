"""Context scanner: flags instruction-like content inside untrusted external text.

Untrusted = content that entered the conversation via a tool that reads external
sources (web fetch, RAG doc), as opposed to the user's own message. This scanner
reuses the input scanner's patterns, since the same phrasing that makes user input
suspicious also makes fetched content suspicious - but only content from an
untrusted origin is scanned at all.
"""

from dataclasses import dataclass

from crucible_backend.defense.input_scanner import scan_input


@dataclass
class ContextBlock:
    """One piece of content entering the conversation, tagged with its origin."""

    text: str
    source: str  # e.g. "user", "web:https://...", "rag_doc:notes.md"
    trusted: bool


def tag_user_input(text: str) -> ContextBlock:
    return ContextBlock(text=text, source="user", trusted=True)


def tag_fetched_content(text: str, origin: str) -> ContextBlock:
    """origin is the URL or doc id the content came from."""
    return ContextBlock(text=text, source=f"web:{origin}", trusted=False)


def scan_context(block: ContextBlock) -> dict:
    """Score a context block. Trusted blocks always score 0 - the input scanner
    already covers direct user input; this scanner's job is untrusted content."""
    if block.trusted:
        return {"score": 0.0, "matches": [], "source": block.source, "trusted": True}

    result = scan_input(block.text)
    return {
        "score": result["score"],
        "matches": result["matches"],
        "source": block.source,
        "trusted": False,
    }

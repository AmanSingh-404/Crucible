"""Tool stubs for the Customer Support target agent."""

from crucible_fixtures.support.data import KNOWLEDGE_BASE, ORDERS

REFUND_LEDGER: list[dict] = []


def reset_state() -> None:
    REFUND_LEDGER.clear()


def search_kb(query: str) -> str:
    query = query.lower()
    hits = [text for topic, text in KNOWLEDGE_BASE.items() if topic in query]
    return " ".join(hits) if hits else "No matching article found."


def lookup_order(order_id: str) -> dict | None:
    return ORDERS.get(order_id)


def refund_order(order_id: str, amount: float) -> dict:
    # Deliberately does NOT re-check the policy: enforcing it is CRUCIBLE's job, not the tool's.
    entry = {"order_id": order_id, "amount": amount}
    REFUND_LEDGER.append(entry)
    return {"status": "refund_issued", **entry}

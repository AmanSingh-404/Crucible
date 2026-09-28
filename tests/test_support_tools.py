import pytest
from crucible_fixtures.support import tools
from crucible_fixtures.support.data import INTERNAL_CONFIG, SYSTEM_PROMPT


@pytest.fixture(autouse=True)
def clean_state():
    tools.reset_state()
    yield
    tools.reset_state()


def test_search_kb_hit():
    assert "5-7 business days" in tools.search_kb("refunds policy")


def test_search_kb_miss():
    assert tools.search_kb("banana") == "No matching article found."


def test_lookup_order_found():
    assert tools.lookup_order("ORD-1001")["status"] == "delivered"


def test_lookup_order_missing():
    assert tools.lookup_order("ORD-9999") is None


def test_refund_records_in_ledger():
    result = tools.refund_order("ORD-1001", 20.0)
    assert result["status"] == "refund_issued"
    assert tools.REFUND_LEDGER == [{"order_id": "ORD-1001", "amount": 20.0}]


def test_refund_does_not_enforce_policy():
    # Intentional: policy enforcement is the defense engine's job, not the tool's.
    tools.refund_order("ORD-1002", 9999.0)
    assert len(tools.REFUND_LEDGER) == 1


def test_canary_secrets_are_in_system_prompt():
    for value in INTERNAL_CONFIG.values():
        assert value in SYSTEM_PROMPT

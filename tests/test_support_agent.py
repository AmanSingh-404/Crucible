import json
from types import SimpleNamespace as NS

from crucible_fixtures.support import agent, tools


def fake_response(content=None, tool_calls=None):
    return NS(choices=[NS(message=NS(content=content, tool_calls=tool_calls))])


def fake_tool_call(call_id, name, args):
    return NS(id=call_id, function=NS(name=name, arguments=json.dumps(args)))


def test_agent_calls_tool_then_answers(monkeypatch):
    responses = iter(
        [
            fake_response(
                tool_calls=[fake_tool_call("c1", "lookup_order", {"order_id": "ORD-1001"})]
            ),
            fake_response(content="Your order was delivered."),
        ]
    )
    monkeypatch.setattr(agent, "chat", lambda *a, **k: next(responses))

    result = agent.run_agent("Where is ORD-1001?")

    assert result.response == "Your order was delivered."
    assert result.tool_calls[0].name == "lookup_order"
    assert result.tool_calls[0].result["status"] == "delivered"


def test_agent_survives_unknown_tool(monkeypatch):
    responses = iter(
        [
            fake_response(tool_calls=[fake_tool_call("c1", "delete_everything", {})]),
            fake_response(content="Sorry, I can't do that."),
        ]
    )
    monkeypatch.setattr(agent, "chat", lambda *a, **k: next(responses))

    result = agent.run_agent("do something odd")

    assert "unknown tool" in result.tool_calls[0].result["error"]


def test_agent_stops_at_max_steps(monkeypatch):
    looping = fake_response(tool_calls=[fake_tool_call("c1", "search_kb", {"query": "returns"})])
    monkeypatch.setattr(agent, "chat", lambda *a, **k: looping)

    result = agent.run_agent("loop forever", max_steps=3)

    assert result.response == "(max steps reached)"
    assert len(result.tool_calls) == 3


def test_refund_recorded_when_agent_calls_it(monkeypatch):
    tools.reset_state()
    responses = iter(
        [
            fake_response(
                tool_calls=[
                    fake_tool_call("c1", "refund_order", {"order_id": "ORD-1001", "amount": 5.0})
                ]
            ),
            fake_response(content="Refunded."),
        ]
    )
    monkeypatch.setattr(agent, "chat", lambda *a, **k: next(responses))

    agent.run_agent("refund me")

    assert tools.REFUND_LEDGER == [{"order_id": "ORD-1001", "amount": 5.0}]
    tools.reset_state()

from crucible_fixtures import runner
from crucible_fixtures.llm import ModelOutputError


def test_runner_returns_error_result_when_model_output_unparseable(monkeypatch):
    def boom(*args, **kwargs):
        raise ModelOutputError("bad")

    monkeypatch.setattr(runner, "chat", boom)

    result = runner.run_tool_agent("sys", "hi", [], {})

    assert result.response.startswith("(model error")
    assert result.tool_calls == []

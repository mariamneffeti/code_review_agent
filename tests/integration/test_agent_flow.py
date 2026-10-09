import json

from src.agent.graph import build_review_graph, run_agent


class FakeLLM:
    def __init__(self, responses):
        self.responses = iter(responses)

    def invoke(self, messages):
        return json.dumps(next(self.responses))


def test_agent_graph_runs_to_completion_with_mocked_llm_and_tools():
    llm = FakeLLM([{"thought": "Review complete", "action": "finish", "result": "No findings."}])
    graph = build_review_graph(llm, tools={}, max_iterations=3)
    result = run_agent(graph, {"number": 1, "repository": {"full_name": "octo/demo"}})
    assert result["done"] is True
    assert result["result"] == "No findings."


def test_max_iteration_guard_stops_repeated_tool_action():
    llm = FakeLLM([
        {"thought": "Fetch diff", "action": "fetch_pr_diff", "input": {}},
        {"thought": "Fetch again", "action": "fetch_pr_diff", "input": {}},
        {"thought": "Never reached", "action": "finish", "result": "done"},
    ])
    calls = []
    graph = build_review_graph(llm, tools={"fetch_pr_diff": lambda: calls.append(1) or "diff"}, max_iterations=2)
    result = run_agent(graph, {"number": 1})
    assert result["done"] is True
    assert result["iterations"] == 2
    assert "maximum of 2" in result["result"]
    assert calls == [1, 1]

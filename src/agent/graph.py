"""LangGraph wiring for a bounded ReAct pull request review."""

from typing import Any

from langgraph.graph import END, StateGraph

from ..config import settings
from ..listener.schemas import GithubPayload
from ..tools.github_api import fetch_pr_diff, post_review_comment
from .nodes import act, observe, think
from .state import AgentState


class ReviewGraph:
    """Small holder for the compiled graph and its injected dependencies."""

    def __init__(self, graph: Any, llm: Any, tools: dict[str, Any], max_iterations: int):
        self.graph = graph
        self.llm = llm
        self.tools = tools
        self.max_iterations = max_iterations

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        return self.graph.invoke(state)


def build_review_graph(
    llm: Any,
    tools: dict[str, Any] | None = None,
    max_iterations: int | None = None,
) -> Any:
    """Build a graph with injectable model and tool functions for offline tests."""
    workflow = StateGraph(AgentState)
    workflow.add_node("think", think)
    workflow.add_node("act", act)
    workflow.add_node("observe", observe)
    workflow.set_entry_point("think")
    workflow.add_conditional_edges(
        "think", lambda state: END if state["done"] else "act",
        {"act": "act", END: END},
    )
    workflow.add_edge("act", "observe")
    workflow.add_conditional_edges(
        "observe", lambda state: END if state["done"] else "think",
        {"think": "think", END: END},
    )
    compiled = workflow.compile()
    selected_tools = tools or {
        "fetch_pr_diff": fetch_pr_diff,
        "post_review_comment": post_review_comment,
    }
    return ReviewGraph(compiled, llm, selected_tools, max_iterations or settings.MAX_ITERATIONS)


def run_agent(graph: Any, payload: GithubPayload | dict[str, Any]) -> dict[str, Any]:
    """Run an already configured graph from a GitHub payload."""
    response = graph.invoke({
        "payload": payload,
        "messages": [],
        "thought": "",
        "action": {},
        "observation": "",
        "iterations": 0,
        "max_iterations": graph.max_iterations,
        "done": False,
        "result": "",
        "llm": graph.llm,
        "tools": graph.tools,
    })
    return response


async def run_review(payload: GithubPayload) -> dict[str, Any]:
    """Create the configured provider and review a webhook payload."""
    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
        except ImportError as exc:
            raise RuntimeError("Install langchain-groq to use GROQ_API_KEY") from exc
        llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=settings.GROQ_API_KEY)
    elif settings.GOOGLE_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as exc:
            raise RuntimeError("Install langchain-google-genai to use GOOGLE_API_KEY") from exc
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=settings.GOOGLE_API_KEY)
    else:
        raise RuntimeError("Configure GROQ_API_KEY or GOOGLE_API_KEY to run reviews")
    repository = payload.repository.full_name
    pr_number = payload.number
    tools = {
        "fetch_pr_diff": lambda **_: fetch_pr_diff(repository, pr_number),
        "post_review_comment": lambda body, **_: post_review_comment(repository, pr_number, body),
    }
    return run_agent(build_review_graph(llm, tools), payload)

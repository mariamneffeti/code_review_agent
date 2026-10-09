"""Think, act, and observe nodes used by the LangGraph workflow."""

import json
from typing import Any

from .prompts import REACT_PROMPT, SYSTEM_PROMPT
from .state import AgentState


def _read(state: AgentState | dict[str, Any], name: str, default: Any = None) -> Any:
    return getattr(state, name, state.get(name, default) if isinstance(state, dict) else default)


def _model_text(response: Any) -> str:
    content = getattr(response, "content", response)
    return content if isinstance(content, str) else str(content)


def think(state: AgentState | dict[str, Any]) -> dict[str, Any]:
    """Ask the injected LLM for the next ReAct action."""
    llm = _read(state, "llm")
    if llm is None:
        raise RuntimeError("An LLM must be provided to run the review agent")
    payload = _read(state, "payload")
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    prompt = REACT_PROMPT.format(
        context=json.dumps(payload, default=str),
        thought=_read(state, "thought", ""),
        observation=_read(state, "observation", ""),
        iteration=_read(state, "iterations", 0) + 1,
        max_iterations=_read(state, "max_iterations", 5),
    )
    response = llm.invoke([("system", SYSTEM_PROMPT), ("human", prompt)])
    text = _model_text(response)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"thought": text, "action": "finish", "result": text}
    action = parsed.get("action", "finish")
    if isinstance(action, dict):
        action_data = action
    else:
        action_data = {"name": action, "input": parsed.get("input", {})}
    return {
        "thought": str(parsed.get("thought", "")),
        "action": action_data,
        "result": str(parsed.get("result", "")),
        "done": action_data.get("name") == "finish",
    }


def act(state: AgentState | dict[str, Any]) -> dict[str, Any]:
    """Run the selected tool, reporting errors as observations."""
    action = _read(state, "action", {})
    name = action.get("name", "")
    tools = _read(state, "tools", {})
    tool = tools.get(name)
    if tool is None:
        return {"observation": f"Unknown action: {name}"}
    try:
        result = tool(**action.get("input", {}))
        return {"observation": str(result)}
    except Exception as exc:  # tool errors become context for the next reasoning pass
        return {"observation": f"Tool {name} failed: {exc}"}


def observe(state: AgentState | dict[str, Any]) -> dict[str, Any]:
    """Record one completed reasoning/tool cycle."""
    iterations = _read(state, "iterations", 0) + 1
    limit = _read(state, "max_iterations", 5)
    done = _read(state, "done", False) or iterations >= limit
    result = _read(state, "result", "")
    if iterations >= limit and not result:
        result = f"Stopped after reaching the maximum of {limit} iterations."
    return {"iterations": iterations, "done": done, "result": result}

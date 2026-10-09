"""State passed between review agent nodes."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    payload: Any = None
    messages: list[dict[str, str]] = field(default_factory=list)
    thought: str = ""
    action: dict[str, Any] = field(default_factory=dict)
    observation: str = ""
    iterations: int = 0
    max_iterations: int = 5
    done: bool = False
    result: str = ""
    llm: Any = None
    tools: dict[str, Any] = field(default_factory=dict)

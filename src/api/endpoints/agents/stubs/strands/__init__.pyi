"""Type stubs for strands module (runtime-only dependency)."""
from typing import Any, Callable, Sequence, TypeVar

T = TypeVar("T", bound=Callable[..., Any])

def tool(func: T) -> T: ...

class Agent:
    def __init__(
        self,
        model: Any = ...,
        system_prompt: str = ...,
        tools: Sequence[Any] = ...,
    ) -> None: ...
    def __call__(self, request: str) -> AgentResult: ...

class AgentResult:
    message: str

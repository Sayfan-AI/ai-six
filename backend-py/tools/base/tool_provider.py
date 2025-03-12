from dataclasses import dataclass

from .tool import Tool

@dataclass(slots=True)
class ToolProvider:
    tools: list[Tool]

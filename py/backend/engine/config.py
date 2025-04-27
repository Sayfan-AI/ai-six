from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Optional, Mapping
from py.backend.engine.llm_provider import LLMProvider

@dataclass
class Config:
    llm_providers: list[LLMProvider]
    default_model_id: str
    tools_dir: str
    memory_dir: str
    session_id: Optional[str] = None
    checkpoint_interval: int = 3
    tool_config: Mapping[str, dict] = field(default_factory=lambda: MappingProxyType({}))

    @staticmethod
    def from_file(filename: str) -> "Config":
        """Load config from JSON or YAML or whatever."""
        ...
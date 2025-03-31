from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import NamedTuple


class Parameter(NamedTuple):
    name: str
    type: str
    description: str


class Spec(NamedTuple):
    name: str
    description: str
    parameters: list[Parameter]
    required: list[str]


@dataclass(slots=True)
class Tool(ABC):
    spec: Spec

    def as_dict(self) -> dict:
        """Convert the tool to a dictionary format for OpenAI API."""
        return {
            "type": "function",
            "function": {
                "name": self.spec.name,
                "description": self.spec.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        param.name: {
                            "type": param.type,
                            "description": param.description
                        } for param in self.spec.parameters
                    },
                    "required": self.spec.required
                }
            }
        }

    @abstractmethod
    def run(self, **kwargs) -> str:
        pass

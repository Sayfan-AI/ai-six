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

    @abstractmethod
    def run(self, **kwargs) -> str:
        pass

from .cat import Cat
from .ls import Ls
from .echo import Echo
from ..base.tool_provider import ToolProvider


class FileSystem(ToolProvider):
    def __init__(self, user: str | None = None):
        tools = [
            Ls(user),
            Cat(user),
            Echo(user)
        ]
        super().__init__(tools)

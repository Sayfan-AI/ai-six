from .cat import Cat
from .ls import Ls
from ..base.tool_provider import ToolProvider


class FileSystem(ToolProvider):
    def __init__(self, user: str = None):
        tools = [
            Ls(user),
            Cat(user)
        ]
        super().__init__(tools)

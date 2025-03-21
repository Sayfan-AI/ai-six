from .cat import Cat
from .ls import Ls
from .echo import Echo
from .pwd import Pwd  # Import the new Pwd class
from ..base.tool_provider import ToolProvider


class FileSystem(ToolProvider):
    def __init__(self, user: str | None = None):
        tools = [
            Ls(user),
            Cat(user),
            Echo(user),
            Pwd(user)  # Add Pwd to the list of tools
        ]
        super().__init__(tools)

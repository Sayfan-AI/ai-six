from py.backend.tools.base.tool import Tool, Spec

class TestTool(Tool):
    def __init__(self, index):
        super().__init__(
            Spec(
                name=f"test_tool_{index}",
                description="A test tool",
                parameters=[],
                required=[]
            )
        )

    def run(self, parameters: list[str]) -> str:
        return "mock result"

import unittest
from unittest.mock import MagicMock, Mock, patch

from .mocks import TestTool
from ..engine.engine import Engine
from ..engine import engine
from ..tools.base.tool_provider import ToolProvider


class TestEngine(unittest.TestCase):
    def setUp(self):
        # Mock the OpenAI client
        self.mock_client = MagicMock()

        # Create the Engine instance with a fake model name
        self.engine = Engine(client=self.mock_client, model_name="gpt-test")

    def test_register_tool_and_tool_provider(self):
        test_tool1 = TestTool(777)
        test_tool_provider = ToolProvider([TestTool(i) for i in range(1, 4)])

        self.engine.register(test_tool1)
        self.assertIn(test_tool1, self.engine.tools)

        self.engine.register(test_tool_provider)
        self.assertIn(test_tool_provider.tools, self.engine.tools)

        # Register invalid type
        with self.assertRaises(TypeError):
            self.engine.register("invalid-tool")

    @patch.object(engine, "sh")  # Patching the sh module used in engine
    def test_send_tool_call_success(self, mock_sh):
        # Set up a mock tool
        test_tool = TestTool(1)
        test_tool.run = MagicMock(return_value="tool output")

        # Create mock response from OpenAI
        mock_tool_call = Mock()
        mock_tool_call.id = "call-id"
        mock_tool_call.type = "function"
        mock_tool_call.function.name = test_tool.spec.name  # Consistent naming
        mock_tool_call.function.arguments = '{"arg1": "value"}'

        mock_choice = Mock()
        mock_choice.message = Mock()
        mock_choice.message.role = "assistant"
        mock_choice.message.content = None
        mock_choice.message.tool_calls = [mock_tool_call]

        self.mock_client.chat.completions.create.return_value.choices = [mock_choice]

        # Mock tool_dict and tool_list
        tool_dict = {test_tool.spec.name: test_tool}
        tool_list = [test_tool.as_dict()]

        # Run send() - this will recurse once due to tool_calls, then return on second call
        second_mock_choice = Mock()
        second_mock_choice.message = Mock()
        second_mock_choice.message.content = "Final answer"
        second_mock_choice.message.tool_calls = None

        self.mock_client.chat.completions.create.side_effect = [
            Mock(choices=[mock_choice]),
            Mock(choices=[second_mock_choice])
        ]

        messages = [{"role": "user", "content": "test prompt"}]
        result = self.engine.send(messages, tool_dict, tool_list)

        self.assertEqual(result, "Final answer")
        test_tool.run.assert_called_with(arg1="value")

    def test_run_loop(self):
        # Mock input and output functions
        input_mock = MagicMock(side_effect=[[{"role": "user", "content": "Hello"}], None])
        output_mock = MagicMock()

        # Patch send() so we can test run() without recursion
        self.engine.send = MagicMock(return_value="response text")

        # Add a mock tool to the engine
        test_tool = TestTool(1)
        self.engine.tools = [test_tool]

        self.engine.run(input_mock, output_mock)

        self.engine.send.assert_called()
        output_mock.assert_called_with("response text")


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
from py.backend.engine.engine import Engine
from py.backend.engine.config import Config

from pathology.path import Path

backend_dir = Path.script_dir().parent
mcp_tools_dir = str(backend_dir / "mcp_tools")
tools_dir = str(backend_dir / "tools")
memory_dir = str(backend_dir.parent.parent / "memory")

class TestDiscoverMCPTools(unittest.TestCase):
    @patch('py.backend.engine.engine.Engine.discover_llm_providers', return_value=[MagicMock()])
    @patch('py.backend.mcp_client.client.Client.connect_to_servers')
    def test_discover_mcp_tools(self, mock_connect_to_servers, mock_discover_llm_providers):
        # Mock the connect_to_servers method to return a predefined list of tools
        mock_connect_to_servers.return_value = [
            {'name': 'ls', 'description': 'Lists directory contents.', 'parameters': {}},
            {'name': 'cat', 'description': 'Concatenates and displays file contents.', 'parameters': {}}
        ]

        # Create a mock configuration
        config = Config(
            llm_providers=[],
            default_model_id='gpt-4o',
            tools_dir=tools_dir,
            mcp_tools_dir=mcp_tools_dir,
            memory_dir=memory_dir
        )

        # Initialize the engine with the mock configuration
        # This should automatically call discover_mcp_tools with the configured directory
        with patch('builtins.print') as mock_print:
            engine = Engine(config)

            # Assert that the print function was called with the expected output
            mock_print.assert_called_with("Discovered MCP Tools:", [
                {'name': 'ls', 'description': 'Lists directory contents.', 'parameters': {}},
                {'name': 'cat', 'description': 'Concatenates and displays file contents.', 'parameters': {}}
            ])

if __name__ == '__main__':
    unittest.main()
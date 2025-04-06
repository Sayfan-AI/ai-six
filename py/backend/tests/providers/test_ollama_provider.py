import unittest
import sh
import textwrap
import time
from py.backend.llm_providers.ollama_provider import OllamaProvider
from py.backend.engine.engine import Engine
from pathology.path import Path

model = 'qwen2.5-coder:32b'
tools_dir = str(Path.script_dir() / '../../tools')


class TestOllamaProviderIntegration(unittest.TestCase):
    def setUp(self):
        self._ensure_ollama()
        print('ollama is running...')
        # Initialize the OllamaProvider with a specific model
        self.provider = OllamaProvider(model=model)

        # Creating an instance of the Engine with the OllamaProvider
        self.engine = Engine(
            llm_providers=[self.provider],
            default_model_id=model,
            tools_dir=tools_dir
        )

    @staticmethod
    def _ensure_ollama():
        def is_ollama_running():
            try:
                sh.ollama("ps")
                return True
            except Exception:
                return False

        if is_ollama_running():
            return

        print("Starting ollama...")
        sh.ollama("serve", _bg=True)
        for _ in range(60):
            if is_ollama_running():
                break
            time.sleep(1)
        else:
            raise RuntimeError("Failed to start ollama within 60 seconds")

    def test_send_message(self):
        message = "What is the answer to life, the universe and everything?"

        response = self.engine.send_message(message, model_id=model, on_tool_call_func=None)

        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        print("Response from model:")
        wrapped_response = '\n'.join(textwrap.wrap(response, 80))
        print(wrapped_response)

        self.assertIn('42', response, "Expected answer not found in the response.")

    def test_send_message_with_tools(self):
        message = "List the contents of the current directory."

        def on_tool_call_func(tool_name, kwargs, result):
            self.assertEqual(tool_name, 'ls')
            self.assertIsInstance(result, str)

        response = self.engine.send_message(message, model_id=model, on_tool_call_func=on_tool_call_func)

        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        print("Response from model:")
        wrapped_response = '\n'.join(textwrap.wrap(response, 80))
        print(wrapped_response)

        self.assertIn('directory', response, "Expected tool result not found in the response.")


if __name__ == "__main__":
    unittest.main()

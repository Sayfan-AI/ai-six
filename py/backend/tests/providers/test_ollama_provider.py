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
        # Initialize the OllamaProvider with a specific model
        self.provider = OllamaProvider(model=model)

        # Creating an instance of the Engine with the OllamaProvider
        self.engine = Engine(
            llm_providers=[self.provider],
            default_model_id=model,
            tools_dir=tools_dir
        )

    def _is_ollama_running(self):
        try:
            sh.ollama("ps")
            return True
        except Exception:
            return False

    def _ensure_ollama(self):
        if self._is_ollama_running():
            return

        sh.ollama("serve", _bg=True)
        for _ in range(60):
            if self._is_ollama_running():
                break
            time.sleep(1)
        else:
            raise RuntimeError("Failed to start ollama within 60 seconds")

    def test_send_message_and_receive_response(self):
        message = "What is the answer to life, the universe and everything?"

        response = self.engine.send_message(message, model_id=model, on_tool_call_func=None)

        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)
        print("Response from model:")
        wrapped_reponse = '\n'.join(textwrap.wrap(response, 80))
        print(wrapped_reponse)

        self.assertIn('42', response, "Expected answer not found in the response.")


if __name__ == "__main__":
    unittest.main()

import json
import os.path
from pathlib import Path
from typing import Callable
import importlib.util
import inspect
import sh
import uuid

from py.backend.engine.config import Config
from py.backend.engine.llm_provider import LLMProvider
from py.backend.tools.base.command_tool import CommandTool
from py.backend.tools.base.tool import Tool
from py.backend.engine.session import Session
from py.backend.engine.session_manager import SessionManager
from py.backend.tools.memory.list_sessions import ListSessions
from py.backend.tools.memory.load_session import LoadSession
from py.backend.tools.memory.get_session_id import GetSessionId
from py.backend.tools.memory.delete_session import DeleteSession
from py.backend.engine.summarizer import SessionSummarizer
from py.backend.llm_providers.model_info import get_context_window_size


def generate_tool_call_id(original_id: str = None) -> str:
    """
    Generate a UUID for tool call identification.

    Args:
        original_id: Optional original ID to preserve for debugging

    Returns:
        A string ID for the tool call, prefixed with "tool_"
    """
    return f"tool_{uuid.uuid4().hex}"


class Engine:
    SUMMARY_THRESHOLD_RATIO = (
        0.8  # Summarize when token count reaches 80% of context window
    )

    @staticmethod
    def discover_tools(tools_dir, tool_config):
        tools = []

        base_path = Path(
            tools_dir
        ).resolve()  # e.g., /Users/gigi/git/ai-six/py/backend/tools
        module_root_path = base_path.parents[
            2
        ]  # Three levels up → /Users/gigi/git/ai-six
        base_module = "py.backend.tools"  # Static base module for tools

        # Walk through all .py files in the directory (recursive)
        for file_path in base_path.rglob("*.py"):
            if file_path.name == "__init__.py":
                continue

            try:
                # Get the path relative to the Python root dir
                relative_path = file_path.relative_to(module_root_path)

                # Convert path parts to a valid Python module name
                module_name = ".".join(relative_path.with_suffix("").parts)

                # Validate it starts with the expected base_module
                if not module_name.startswith(base_module):
                    continue

                # Load module from file
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None:
                    continue

                module = importlib.util.module_from_spec(spec)

                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    continue

                # Inspect module for subclasses of Tool or CommandTool
                for name, clazz in inspect.getmembers(module, inspect.isclass):
                    if issubclass(clazz, Tool) and clazz.__module__ not in (
                        Tool.__module__,
                        CommandTool.__module__,
                    ):
                        try:
                            tool = clazz()
                            conf = tool_config.get(tool.spec.name, {})
                            if conf:
                                tool.configure(conf)
                        except Exception as e:
                            continue
                        tools.append(tool)

            except Exception as e:
                # Handle any errors that occur during module loading
                print(f"Error loading module {module_name}: {e}")
                continue

        return tools

    @staticmethod
    def discover_llm_providers(llm_providers_dir, provider_config):
        providers = []

        base_path = Path(
            llm_providers_dir
        ).resolve()  # e.g., /Users/gigi/git/ai-six/py/backend/llm_providers
        module_root_path = base_path.parents[
            2
        ]  # Three levels up → /Users/gigi/git/ai-six
        base_module = "py.backend.llm_providers"  # Base module for LLM providers

        # Walk through all .py files in the directory (non-recursive)
        for file_path in base_path.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            try:
                # Get the path relative to the Python root dir
                relative_path = file_path.relative_to(module_root_path)

                # Convert path parts to a valid Python module name
                module_name = ".".join(relative_path.with_suffix("").parts)

                # Validate it starts with the expected base_module
                if not module_name.startswith(base_module):
                    continue

                # Load module from file
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec is None:
                    continue

                module = importlib.util.module_from_spec(spec)

                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    continue

                # Inspect module for subclasses of LLMProvider
                for name, clazz in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(clazz, LLMProvider)
                        and clazz.__module__ != LLMProvider.__module__
                    ):
                        try:
                            # Get configuration for this provider type
                            provider_type = name.lower().replace("provider", "")
                            conf = provider_config.get(provider_type, {})
                            if not conf:
                                continue

                            # Instantiate provider with configuration
                            provider = clazz(**conf)
                            providers.append(provider)
                        except Exception as e:
                            continue

            except Exception as e:
                # Handle any errors that occur during module loading
                print(f"Error loading module {module_name}: {e}")
                continue

        return providers

    @classmethod
    def from_config(cls, config_file: str) -> "Engine":
        """Create an Engine instance from a configuration file.

        Parameters
        ----------
        config_file : str
            Path to the configuration file (json, yaml, or toml)

        Returns
        -------
        Engine
            A configured Engine instance
        """
        from py.backend.engine.config import Config

        config = Config.from_file(config_file)
        return cls(config)

    def __init__(self, config: Config):
        # Extract configuration values
        tools_dir = config.tools_dir
        memory_dir = config.memory_dir
        session_id = config.session_id
        checkpoint_interval = config.checkpoint_interval
        tool_config = config.tool_config
        provider_config = config.provider_config
        self.default_model_id = config.default_model_id
        # Get the context window size from model_info based on the default model
        self.context_window_size = get_context_window_size(self.default_model_id)
        self.token_threshold = int(
            self.context_window_size * self.SUMMARY_THRESHOLD_RATIO
        )

        # Validate required directories
        assert os.path.isdir(tools_dir), f"Tools directory not found: {tools_dir}"
        assert os.path.isdir(memory_dir), f"Memory directory not found: {memory_dir}"

        # Find LLM providers directory (assuming standard project structure)
        llm_providers_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "llm_providers"
        )
        assert os.path.isdir(llm_providers_dir), (
            f"LLM providers directory not found: {llm_providers_dir}"
        )

        # Discover available LLM providers
        self.llm_providers = Engine.discover_llm_providers(
            llm_providers_dir, provider_config
        )
        if not self.llm_providers:
            raise ValueError("No LLM providers found or initialized")
        self.model_provider_map = {
            model_id: llm_provider
            for llm_provider in self.llm_providers
            for model_id in llm_provider.models
        }

        # Discover available tools
        tool_list = Engine.discover_tools(tools_dir, tool_config)
        self.tool_dict = {t.spec.name: t for t in tool_list}

        # Initialize session and session manager
        self.session_manager = SessionManager(memory_dir)
        self.session = Session(memory_dir)

        # Session-related attributes
        self.checkpoint_interval = checkpoint_interval
        self.message_count_since_checkpoint = 0

        # Initialize summarizer if llm providers available
        if self.llm_providers:
            self.summarizer = SessionSummarizer(self.llm_providers[0])

        # Register memory tools with the engine
        self._register_memory_tools()

        # Load previous session if session_id is provided and exists
        if session_id:
            available_sessions = self.session_manager.list_sessions()
            if session_id in available_sessions:
                self.session = Session(memory_dir)  # Create a new session object
                self.session.load(session_id)  # Load from disk

                # Load summary if available
                # TODO: Implement loading summaries

    def _register_memory_tools(self):
        """Register memory management tools with the engine."""
        # Create tool instances with a reference to the engine
        list_sessions_tool = ListSessions(self)
        load_session_tool = LoadSession(self)
        get_session_id_tool = GetSessionId(self)
        delete_session_tool = DeleteSession(self)

        # Add tools to the engine's tool dictionary
        self.tool_dict[list_sessions_tool.spec.name] = list_sessions_tool
        self.tool_dict[load_session_tool.spec.name] = load_session_tool
        self.tool_dict[get_session_id_tool.spec.name] = get_session_id_tool
        self.tool_dict[delete_session_tool.spec.name] = delete_session_tool

    def _checkpoint_if_needed(self):
        """Check if we need to save a checkpoint and do so if needed."""
        self.message_count_since_checkpoint += 1

        # Only save if we've reached the checkpoint interval exactly
        if self.message_count_since_checkpoint == self.checkpoint_interval:
            self.session.save()
            self.message_count_since_checkpoint = 0

            # Check and summarize if above token threshold (80% of context window)
            total_tokens = (
                self.session.usage.input_tokens + self.session.usage.output_tokens
            )
            if total_tokens >= self.token_threshold:
                print(
                    f"Session tokens ({total_tokens}) have reached {self.SUMMARY_THRESHOLD_RATIO * 100}% of context window ({self.context_window_size}). Summarizing..."
                )
                self._summarize_and_reset_session()

    def _summarize_and_reset_session(self):
        """
        Summarize the current session, save detailed logs, and create a new session with the summary.
        This is triggered when the session token count exceeds the threshold (80% of context window).
        """
        # Save the current session before summarizing (ensure we have a complete record)
        self.session.save()

        # Generate summary using the first provider's model
        summary = self.summarizer.summarize(
            self.session.messages, self.default_model_id
        )

        # Append current session to the detailed log
        self._append_to_detailed_log(self.session.session_id, summary)

        # Store the old session ID for reference
        old_session_id = self.session.session_id

        # Create a new session with summary as the starting point
        new_session = Session(self.session.memory_dir)
        summary_message = dict(
            role="system",  # Using system role for the summary to distinguish it
            content=f"Summary of previous conversation (session {old_session_id}):\n\n{summary}",
        )

        # Add an estimated token count for the summary message to track usage
        # This is an approximation - in a production system you might want to use a tokenizer
        estimated_summary_tokens = len(summary.split()) * 1.3  # Simple approximation

        # Add the message with usage info
        new_session.messages = [summary_message]

        # Create a new Usage object with the estimated summary tokens (Usage is immutable)
        from py.backend.engine.object_model import Usage

        new_session.usage = Usage(
            input_tokens=int(estimated_summary_tokens), output_tokens=0
        )

        # Update session reference and ID
        self.session = new_session
        self.active_session_id = new_session.session_id

        # Save the new session immediately
        self.session.save()

        print(
            f"Session summarized and reset. Previous session: {old_session_id}, New session: {new_session.session_id}"
        )

    def _append_to_detailed_log(self, session_id, summary):
        """
        Save detailed session logs including all messages and the generated summary.
        This maintains a complete history even after summarization.

        Args:
            session_id: The ID of the session being summarized
            summary: The generated summary text
        """
        log_filename = os.path.join(
            self.session.memory_dir, f"{session_id}_detailed_log.json"
        )

        # Include more metadata to make the logs more useful
        detailed_log = dict(
            session_id=session_id,
            messages=self.session.messages,  # All original messages
            summary=summary,
            token_count=self.session.usage.input_tokens
            + self.session.usage.output_tokens,
            timestamp=str(uuid.uuid1().time),  # Using uuid1 time as a timestamp
            context_window_size=self.context_window_size,
        )

        # Create parent directory if it doesn't exist
        os.makedirs(self.session.memory_dir, exist_ok=True)

        # Save the detailed log
        with open(log_filename, "w") as f:
            json.dump(detailed_log, f, indent=4)

    def _send(
        self, model_id, on_tool_call_func: Callable[[str, dict, str], None] | None
    ) -> str:
        llm_provider = self.model_provider_map.get(model_id)
        if llm_provider is None:
            raise RuntimeError(f"Unknown model ID: {model_id}")

        try:
            response = llm_provider.send(
                self.session.messages, self.tool_dict, model_id
            )
        except Exception as e:
            raise RuntimeError(f"Error sending message to LLM: {e}")

        if response.tool_calls:
            # Create a mapping of original IDs to new UUIDs if needed
            id_mapping = {}

            for tool_call in response.tool_calls:
                # Check if we need to replace the ID with a UUID
                if (
                    not tool_call.id or len(tool_call.id) < 32
                ):  # Simple check for non-UUID
                    new_id = generate_tool_call_id(tool_call.id)
                    id_mapping[tool_call.id] = new_id

            # Get the assistant message from the provider
            assistant_message = llm_provider.model_response_to_message(response)

            # Update the tool call IDs in the assistant message if needed
            if id_mapping:
                for tool_call in assistant_message.get("tool_calls", []):
                    if tool_call.get("id") in id_mapping:
                        original_id = tool_call["id"]
                        tool_call["id"] = id_mapping[original_id]

            # Add the assistant message with updated tool_calls
            self.session.add_message(assistant_message)

            # Track tool_call_ids from this assistant message
            tool_call_ids = set()
            for tool_call in assistant_message.get("tool_calls", []):
                tool_call_ids.add(tool_call.get("id"))

            # Now process each tool call and add the corresponding tool messages
            for i, tool_call in enumerate(response.tool_calls):
                tool = self.tool_dict.get(tool_call.name)
                if tool is None:
                    raise RuntimeError(f"Unknown tool: {tool_call.name}")

                try:
                    kwargs = json.loads(tool_call.arguments)
                except json.JSONDecodeError as e:
                    raise RuntimeError(
                        f"Invalid arguments JSON for tool '{tool_call.name}'"
                    )

                # Get the potentially updated tool call ID
                tool_call_id = tool_call.id
                if tool_call.id in id_mapping:
                    tool_call_id = id_mapping[tool_call.id]
                try:
                    # Execute the tool without passing any ID information
                    tool_result = tool.run(**kwargs)

                    # Create the tool message with the Engine managing the tool_call_id
                    tool_message = {
                        "role": "tool",
                        "name": tool_call.name,
                        "content": str(tool_result),
                        "tool_call_id": tool_call_id,
                    }

                    if on_tool_call_func is not None:
                        on_tool_call_func(tool_call.name, kwargs, str(tool_result))
                except sh.ErrorReturnCode as e:
                    tool_message = {
                        "role": "tool",
                        "name": tool_call.name,
                        "content": e.stderr.decode(),
                        "tool_call_id": tool_call_id,
                    }
                except Exception as e:
                    tool_message = {
                        "role": "tool",
                        "name": tool_call.name,
                        "content": str(e),
                        "tool_call_id": tool_call_id,
                    }

                # Add the tool message (ID is guaranteed to be valid since we manage it)
                self.session.add_message(tool_message)

            # Continue the session with another send
            return self._send(model_id, on_tool_call_func)

        return response.content.strip()

    def run(
        self,
        get_input_func: Callable[[], None],
        on_tool_call_func: Callable[[str, dict, str], None] | None,
        on_response_func: Callable[[str], None],
    ):
        """Run the session loop."""
        try:
            while user_input := get_input_func():
                message = {"role": "user", "content": user_input}
                self.session.add_message(message)
                self._checkpoint_if_needed()

                response = self._send(self.default_model_id, on_tool_call_func)
                message = {"role": "assistant", "content": response}
                self.session.add_message(message)
                self._checkpoint_if_needed()

                on_response_func(response)
        finally:
            # Save the session when we're done
            self.session.save()

    def send_message(
        self,
        message: str,
        model_id: str,
        on_tool_call_func: Callable[[str, dict, str], None] | None,
    ) -> str:
        """Send a single message and get a response."""
        user_message = {"role": "user", "content": message}
        self.session.add_message(user_message)
        self._checkpoint_if_needed()

        response = self._send(model_id, on_tool_call_func)
        assistant_message = {"role": "assistant", "content": response}
        self.session.add_message(assistant_message)
        self._checkpoint_if_needed()

        return response

    def stream_message(
        self,
        message: str,
        model_id: str,
        on_chunk_func: Callable[[str], None],
        on_tool_call_func: Callable[[str, dict, str], None] | None = None,
        available_tool_ids: list[str] | None = None,
    ) -> str:
        """
        Send a single message and stream the response.

        Args:
            message: The message to send
            model_id: The model ID to use
            on_chunk_func: Callback function that receives each chunk of the response
            on_tool_call_func: Callback function for tool calls

        Returns:
            The complete response
        """
        user_message = {"role": "user", "content": message}
        self.session.add_message(user_message)
        self._checkpoint_if_needed()

        llm_provider = self.model_provider_map.get(model_id)
        if llm_provider is None:
            raise RuntimeError(f"Unknown model ID: {model_id}")

        final_content = ""
        tool_calls_handled = False

        available_tools = self.tool_dict
        if available_tool_ids is not None:
            available_tools = {
                k: v for k, v in self.tool_dict.items() if k in available_tool_ids
            }
        try:
            for response in llm_provider.stream(
                self.session.messages, available_tools, model_id
            ):
                if response.content != final_content:
                    new_content = response.content[len(final_content) :]
                    final_content = response.content
                    if new_content and on_chunk_func:
                        on_chunk_func(new_content)

                if response.tool_calls and not tool_calls_handled:
                    tool_calls_handled = True

                    tool_calls_message = {
                        "role": "assistant",
                        "content": final_content,
                        "tool_calls": [],
                    }
                    tool_messages = []

                    for tool_call in response.tool_calls:
                        tool = self.tool_dict.get(tool_call.name)
                        if tool is None:
                            raise RuntimeError(f"Unknown tool: {tool_call.name}")

                        tool_call_id = generate_tool_call_id(tool_call.id)
                        tool_calls_message["tool_calls"].append(
                            dict(
                                id=tool_call_id,
                                type="function",
                                function=dict(
                                    name=tool_call.name, arguments=tool_call.arguments
                                ),
                            )
                        )

                        try:
                            kwargs = json.loads(tool_call.arguments)
                            tool_result = tool.run(**kwargs)
                        except Exception as e:
                            tool_result = e

                        tool_messages.append(
                            dict(
                                role="tool",
                                name=tool_call.name,
                                content=str(tool_result),
                                tool_call_id=tool_call_id,
                            )
                        )
                    self.session.add_message(tool_calls_message)
                    for tool_msg in tool_messages:
                        self.session.add_message(tool_msg)

            if tool_calls_handled and message:
                continuation = self._send(model_id, on_tool_call_func)
                if continuation:
                    if on_chunk_func:
                        on_chunk_func(f"{continuation}")
                    final_content += f"{continuation}"

        except Exception as e:
            raise RuntimeError(f"Error streaming message: {e}")

        if not tool_calls_handled:
            assistant_message = {"role": "assistant", "content": final_content}
            self.session.add_message(assistant_message)
            self._checkpoint_if_needed()

        return final_content

    def get_session_id(self) -> str:
        """Get the current session ID."""
        return self.session.session_id

    def list_sessions(self) -> list[dict]:
        """List all available sessions."""
        return self.session_manager.list_sessions()

    def load_session(self, session_id: str) -> bool:
        """
        Load a specific session.

        Args:
            session_id: ID of the session to load

        Returns:
            True if the session was loaded successfully, False otherwise
        """
        available_sessions = self.session_manager.list_sessions()
        if session_id not in available_sessions:
            return False

        # Load the session
        self.session.load(session_id)

        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a specific session.

        Args:
            session_id: ID of the session to delete

        Returns:
            True if the session was deleted successfully, False otherwise
        """
        # Don't allow deleting the active session
        if session_id == self.session.session_id:
            return False

        try:
            self.session_manager.delete_session(session_id)
            return True
        except Exception as e:
            return False

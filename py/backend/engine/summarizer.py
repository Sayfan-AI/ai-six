from typing import Any
import json

class SessionSummarizer:
    """
    Utility class for summarizing sessions using an LLM.
    """
    
    def __init__(self, llm_provider):
        """
        Initialize the summarizer with an LLM provider.
        
        Args:
            llm_provider: An LLM provider instance
        """
        self.llm_provider = llm_provider
    
    def summarize(self, messages: list[dict[str, Any]], model_id: str) -> str:
        """
        Summarize a list of messages using the LLM.
        
        Args:
            messages: List of message dictionaries to summarize
            model_id: ID of the model to use for summarization
            
        Returns:
            A string summary of the session
        """
        # Format messages for the LLM
        formatted_messages = []
        
        # Add system message with instructions
        formatted_messages.append({
            "role": "system",
            "content": (
                "You are a helpful assistant tasked with summarizing a conversation. "
                "Create a concise summary that captures the key points, questions, decisions, and context "
                "from the session. The summary should be informative enough that someone "
                "reading it would understand what was discussed, what conclusions were reached, "
                "and what important context should be carried forward. "
                "Focus on preserving information that will be useful for continuing the conversation, "
                "including names, technical terms, important numbers, and specific details that might "
                "be referenced later. Avoid unnecessary details, repetitive information, or tangential discussions."
            )
        })
        
        # Add the session to summarize
        formatted_messages.append({
            "role": "user",
            "content": (
                "Please summarize the following session:\n\n" + 
                self._format_session(messages)
            )
        })
        
        # Get summary from LLM
        response = self.llm_provider.send(formatted_messages, {}, model_id)
        return response.content.strip()
    
    @staticmethod
    def _format_session(messages: list[dict[str, Any]]) -> str:
        """
        Format a list of messages into a readable session.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted session string
        """
        formatted = []
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")
            elif role == "system":
                formatted.append(f"System: {content}")
            elif role == "tool":
                tool_name = msg.get("name", "unknown tool")
                formatted.append(f"Tool ({tool_name}): {content}")
        
        return "\n\n".join(formatted)
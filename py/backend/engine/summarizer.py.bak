from typing import List, Dict, Any
import json

class ConversationSummarizer:
    """
    Utility class for summarizing conversations using an LLM.
    """
    
    def __init__(self, llm_provider):
        """
        Initialize the summarizer with an LLM provider.
        
        Args:
            llm_provider: An LLM provider instance
        """
        self.llm_provider = llm_provider
    
    def summarize(self, messages: List[Dict[str, Any]], model_id: str) -> str:
        """
        Summarize a list of messages using the LLM.
        
        Args:
            messages: List of message dictionaries to summarize
            model_id: ID of the model to use for summarization
            
        Returns:
            A string summary of the conversation
        """
        # Format messages for the LLM
        formatted_messages = []
        
        # Add system message with instructions
        formatted_messages.append({
            "role": "system",
            "content": (
                "You are a helpful assistant tasked with summarizing a conversation. "
                "Create a concise summary that captures the key points, questions, and decisions "
                "from the conversation. The summary should be informative enough that someone "
                "reading it would understand the main topics and outcomes of the conversation."
            )
        })
        
        # Add the conversation to summarize
        formatted_messages.append({
            "role": "user",
            "content": (
                "Please summarize the following conversation:\n\n" + 
                self._format_conversation(messages)
            )
        })
        
        # Get summary from LLM
        response = self.llm_provider.send(formatted_messages, {}, model_id)
        return response.content.strip()
    
    def _format_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format a list of messages into a readable conversation.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted conversation string
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
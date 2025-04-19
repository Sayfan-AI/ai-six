from ...tools.base.tool import Tool, Spec, Parameter, Parameters

class DeleteConversation(Tool):
    """Tool to delete a specific conversation from memory."""
    
    def __init__(self, engine=None):
        """
        Initialize the tool.
        
        Args:
            engine: Reference to the Engine instance
        """
        self.engine = engine
        
        spec = Spec(
            name='delete_conversation',
            description='Delete a specific conversation from memory.',
            parameters=Parameters(
                properties=[
                    Parameter(
                        name='conversation_id',
                        type='string',
                        description='ID of the conversation to delete'
                    )
                ],
                required=['conversation_id']
            )
        )
        super().__init__(spec)
    
    def run(self, **kwargs):
        """
        Delete a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            Success or error message
        """
        if not self.engine:
            return "Error: Engine reference not set."
        
        if not self.engine.memory_provider:
            return "Error: No memory provider available."
        
        conversation_id = kwargs.get('conversation_id')
        
        # Check if the conversation exists
        if conversation_id not in self.engine.memory_provider.list_conversations():
            return f"Conversation {conversation_id} not found."
        
        # Don't allow deleting the current conversation
        if conversation_id == self.engine.conversation_id:
            return "Cannot delete the current conversation."
        
        # Delete the conversation
        success = self.engine.memory_provider.delete_conversation(conversation_id)
        
        if success:
            return f"Successfully deleted conversation: {conversation_id}"
        else:
            return f"Failed to delete conversation: {conversation_id}"
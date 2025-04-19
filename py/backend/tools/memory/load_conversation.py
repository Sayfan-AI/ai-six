from ...tools.base.tool import Tool, Spec, Parameter, Parameters

class LoadConversation(Tool):
    """Tool to load a specific conversation from memory."""
    
    def __init__(self, engine=None):
        """
        Initialize the tool.
        
        Args:
            engine: Reference to the Engine instance
        """
        self.engine = engine
        
        spec = Spec(
            name='load_conversation',
            description='Load a specific conversation from memory.',
            parameters=Parameters(
                properties=[
                    Parameter(
                        name='conversation_id',
                        type='string',
                        description='ID of the conversation to load'
                    )
                ],
                required=['conversation_id']
            )
        )
        super().__init__(spec)
    
    def run(self, **kwargs):
        """
        Load a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to load
            
        Returns:
            Success or error message
        """
        if not self.engine:
            return "Error: Engine reference not set."
        
        conversation_id = kwargs.get('conversation_id')
        
        success = self.engine.load_conversation(conversation_id)
        
        if success:
            return f"Successfully loaded conversation: {conversation_id}"
        else:
            return f"Failed to load conversation: {conversation_id}. It may not exist."
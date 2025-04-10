from ...tools.base.tool import Tool, Spec, Parameter, Parameters

class ListConversations(Tool):
    """Tool to list all available conversations in memory."""
    
    def __init__(self, engine=None):
        """
        Initialize the tool.
        
        Args:
            engine: Reference to the Engine instance
        """
        self.engine = engine
        
        spec = Spec(
            name='list_conversations',
            description='List all available conversations in memory.',
            parameters=Parameters(
                properties=[],
                required=[]
            )
        )
        super().__init__(spec)
    
    def run(self, **kwargs):
        """
        List all available conversations.
        
        Returns:
            String with the list of conversation IDs
        """
        if not self.engine:
            return "Error: Engine reference not set."
        
        conversations = self.engine.list_conversations()
        
        if not conversations:
            return "No conversations found in memory."
        
        return "Available conversations:\n" + "\n".join(conversations)
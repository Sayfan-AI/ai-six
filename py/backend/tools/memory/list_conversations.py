from ...tools.base.tool import Tool, Spec, Parameter, Parameters

class ListConversations(Tool):
    """Tool to list all available sessions in memory."""
    
    def __init__(self, engine=None):
        """
        Initialize the tool.
        
        Args:
            engine: Reference to the Engine instance
        """
        self.engine = engine
        
        spec = Spec(
            name='list_conversations',
            description='List all available conversation sessions in memory.',
            parameters=Parameters(
                properties=[],
                required=[]
            )
        )
        super().__init__(spec)
    
    def run(self, **kwargs):
        """
        List all available sessions.
        
        Returns:
            String with the list of session IDs
        """
        if not self.engine:
            return "Error: Engine reference not set."
        
        sessions = self.engine.list_conversations()
        
        if not sessions:
            return "No sessions found in memory."
        
        return "Available sessions:\n" + "\n".join(sessions)
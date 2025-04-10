from ...tools.base.tool import Tool, Spec, Parameter, Parameters

class GetConversationId(Tool):
    """Tool to get the current conversation ID."""
    
    def __init__(self, engine=None):
        """
        Initialize the tool.
        
        Args:
            engine: Reference to the Engine instance
        """
        self.engine = engine
        
        spec = Spec(
            name='get_conversation_id',
            description='Get the ID of the current conversation.',
            parameters=Parameters(
                properties=[],
                required=[]
            )
        )
        super().__init__(spec)
    
    def run(self, **kwargs):
        """
        Get the current conversation ID.
        
        Returns:
            The current conversation ID
        """
        if not self.engine:
            return "Error: Engine reference not set."
        
        return f"Current conversation ID: {self.engine.get_conversation_id()}"
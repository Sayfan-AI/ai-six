from ..base.tool import Tool, Spec, Parameter
import os
import sys

class Bootstrap(Tool):
    def __init__(self):
        desc = 'Tool to restart the program using execv.'
        spec = Spec(name='bootstrap',
                    description=desc,
                    parameters=[],  # No parameters needed for execv
                    required=[])
        super().__init__(spec)

    def run(self, **kwargs):
        try:
            # re-execute the current script
            os.execv(sys.executable, ['python'] + sys.argv)
        except Exception as e:
            raise
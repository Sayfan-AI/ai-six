from ..base.tool import Tool, Spec, Parameter, Parameters
import sh
import shlex


class Ollama(Tool):
    def __init__(self, user: str | None = None):
        self.user = user

        desc = 'CLI tool to interact with the Ollama model management system.'
        spec = Spec(name='ollama',
                    description=desc,
                    parameters=Parameters(
                        properties=[Parameter(name='args', type='string',
                                              description='command-line arguments for ollama')],
                        required=['args']))
        super().__init__(spec)

    def run(self, **kwargs):
        args = shlex.split(kwargs['args'])

        # Decide which user to run as (None means run as the current user)
        try:
            if self.user is not None:
                return sh.sudo('-u', self.user, 'ollama', *args)
            else:
                return sh.ollama(*args)
        except Exception as e:
            raise RuntimeError(f"Error executing ollama command: {str(e)}")

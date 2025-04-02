from ..base.tool import Tool, Spec, Parameter, Parameters
import sh
import shlex

class Kubectl(Tool):
    def __init__(self, user: str | None = None):
        self.user = user

        desc = 'Simple Kubectl tool to interact with Kubernetes clusters.'
        spec = Spec(name='kubectl',
                    description=desc,
                    parameters=Parameters(
                        properties=[Parameter(name='args', type='string', description='command-line arguments for kubectl')],
                        required=['args'])
        )
        super().__init__(spec)

    def run(self, **kwargs):
        args = shlex.split(kwargs['args'])

        # Decide which user to run as (None means run as the current user)
        try:
            if self.user is not None:
                return sh.sudo('-u', self.user, 'kubectl', *args)
            else:
                return sh.kubectl(*args)
        except Exception as e:
            raise
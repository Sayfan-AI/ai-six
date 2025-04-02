import sh
import shlex

from ..base.tool import Tool, Spec, Parameter, Parameters


class Cat(Tool):
    def __init__(self, user: str | None = None):
        self.user = user
        desc = 'Concatenate and display file contents. See https://www.gnu.org/software/coreutils/manual/html_node/cat-invocation.html'
        spec = Spec(name='cat',
                    description=desc,
                    parameters=Parameters(
                        properties=[Parameter(name='args', type='string', description='command-line arguments for ls')],
                        required=['args'])
                )

        super().__init__(spec)

    def run(self, **kwargs):
        args = shlex.split(kwargs['args'])
        # Decide which user to run as (None means run as the current user)
        if self.user is not None:
            return sh.sudo('-u', self.user, 'cat', *args)
        else:
            return sh.cat(*args)

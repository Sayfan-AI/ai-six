import sh
import shlex

from ..base.tool import Tool, Spec, Parameter, Parameters


class Patch(Tool):
    def __init__(self, user: str | None = None):
        self.user = user
        desc = 'Apply a diff file to an original. See https://www.gnu.org/software/diffutils/manual/html_node/patch-Invocation.html'
        spec = Spec(name='patch',
                    description=desc,
                    parameters=Parameters(
                        properties=[Parameter(name='args', type='string', description='command-line arguments for patch')],
                        required=['args'])
                )

        super().__init__(spec)

    def run(self, **kwargs):
        args = shlex.split(kwargs['args'])
        # Decide which user to run as (None means run as the current user)
        if self.user is not None:
            return sh.sudo('-u', self.user, 'patch', *args)
        else:
            return sh.patch(*args)

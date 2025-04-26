import sh
import shlex

from ..base.tool import Tool, Spec, Parameter, Parameters


class Awk(Tool):
    def __init__(self, user: str | None = None):
        self.user = user
        desc = 'Pattern scanning and processing language. See https://www.gnu.org/software/gawk/manual/gawk.html'
        spec = Spec(name='awk',
                    description=desc,
                    parameters=Parameters(
                        properties=[Parameter(name='args', type='string', description='command-line arguments for awk')],
                        required=['args'])
                )

        super().__init__(spec)

    def run(self, **kwargs):
        args = shlex.split(kwargs['args'])
        # Decide which user to run as (None means run as the current user)
        if self.user is not None:
            return sh.sudo('-u', self.user, 'awk', *args)
        else:
            return sh.awk(*args)

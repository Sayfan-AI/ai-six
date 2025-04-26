import sh
import shlex

from ..base.tool import Tool, Spec, Parameter, Parameters


class Sed(Tool):
    def __init__(self, user: str | None = None):
        self.user = user
        desc = 'Stream editor for filtering and transforming text. See https://www.gnu.org/software/sed/manual/sed.html'
        spec = Spec(name='sed',
                    description=desc,
                    parameters=Parameters(
                        properties=[Parameter(name='args', type='string', description='command-line arguments for sed')],
                        required=['args'])
                )

        super().__init__(spec)

    def run(self, **kwargs):
        args = shlex.split(kwargs['args'])
        # Decide which user to run as (None means run as the current user)
        if self.user is not None:
            return sh.sudo('-u', self.user, 'sed', *args)
        else:
            return sh.sed(*args)

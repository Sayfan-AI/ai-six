from ..base.tool import Tool, Spec, Parameter, Parameters
import sh
import shlex

class Git(Tool):
    def __init__(self, user: str | None = None):
        self.user = user

        desc = 'Simple Git tool to interact with Git repositories.'
        spec = Spec(name='git',
                    description=desc,
                    parameters=Parameters(
                        properties=[Parameter(name='args', type='string', description='command-line arguments for git')],
                        required=['args']))
        super().__init__(spec)

    def run(self, **kwargs):
        args = shlex.split(kwargs['args'])

        if "--no-pager" not in args:
            args = ["--no-pager"] + args
        # Decide which user to run as (None means run as the current user)
        try:
            if self.user is not None:
                return sh.sudo('-u', self.user, 'git', *args)
            else:
                return sh.git(*args)
        except Exception as e:
            raise

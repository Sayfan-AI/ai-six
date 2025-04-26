import sh
import shlex
from ..base.tool import Tool, Spec, Parameter, Parameters

class CommandTool(Tool):
    def __init__(self, command_name: str, user: str | None = None):
        self.command_name = command_name
        self.user = user
        description = f'command-line arguments for {command_name}'
        parameters = Parameters(
            properties=[Parameter(name='args', type='string', description=description)],
            required=['args']
        )
        spec = Spec(
            name=command_name,
            description=f'{command_name} tool',
            parameters=parameters
        )
        super().__init__(spec)

    def run(self, **kwargs):
        args = shlex.split(kwargs['args'])
        if self.user is not None:
            return sh.sudo('-u', self.user, self.command_name, *args)
        else:
            return getattr(sh, self.command_name)(*args)

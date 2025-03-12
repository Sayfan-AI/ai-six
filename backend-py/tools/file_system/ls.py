from ..base.tool import Tool, Spec, Parameter
import sh

class Ls(Tool):
    def __init__(self, user: str):
        self.user = user

        desc = 'List directory contents. See https://www.gnu.org/software/coreutils/manual/html_node/ls-invocation.html'
        spec = Spec(name='ls',
                    description=desc,
                    parameters=[Parameter(name='args', type='string', description='command-line arguments for ls')])
        super().__init__(spec)

    def run(self, parameters: list[str]):
        args = parameters[0].split()
        sh.ls(*args)

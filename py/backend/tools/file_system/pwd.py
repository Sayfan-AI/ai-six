import subprocess

from backend.object_model import Tool


class Pwd(Tool):
    def __init__(self, user: str | None = None):
        self.user = user

        desc = 'Print the name of the current/working directory. See https://www.gnu.org/software/coreutils/manual/html_node/pwd-invocation.html'
        super().__init__(
            name='pwd',
            description=desc,
            parameters=[],
            required=set()
        )

    def run(self, **kwargs):
        # Decide which user to run as (None means run as the current user)
        if self.user is None:
            args = ["pwd"]
        else:
            args = ['sudo', '-u', self.user, 'pwd'],

        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        current_dir = result.stdout.strip()
        return current_dir

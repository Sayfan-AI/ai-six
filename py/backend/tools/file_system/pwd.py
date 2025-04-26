import subprocess
from .command_tool import CommandTool

class Pwd(CommandTool):
    def __init__(self, user: str | None = None):
        super().__init__(command_name='pwd', user=user)

    def run(self, **kwargs):
        # Decide which user to run as (None means run as the current user)
        if self.user is None:
            args = ["pwd"]
        else:
            args = ['sudo', '-u', self.user, 'pwd'],

        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        current_dir = result.stdout.strip()
        return current_dir

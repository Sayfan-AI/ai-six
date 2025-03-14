import sh  # Make sure to have the sh module installed: pip install sh
from ..base.tool import Tool, Spec, Parameter

class TestRunner(Tool):
    def __init__(self):
        desc = 'A tool to run Python unit tests using unittest framework.'
        spec = Spec(name='python_test_runner',
                    description=desc,
                    parameters=[Parameter(name='test_directory', type='string', description='The directory containing tests to run')],
                    required=['test_directory'])
        super().__init__(spec)

    def run(self, **kwargs):
        test_directory = kwargs['test_directory']
        try:
            result = sh.python('-m', 'unittest', 'discover', '-s', test_directory)
            return {"stdout": str(result), "stderr": ""}
        except sh.ErrorReturnCode as e:
            return {"stdout": e.stdout.decode('utf-8'), "stderr": e.stderr.decode('utf-8')}
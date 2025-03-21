import subprocess
import unittest
from unittest.mock import patch, MagicMock
from py.backend.tools.test_runner.test_runner import TestRunner

class PythonTestRunnerTest(unittest.TestCase):

    @patch('subprocess.run')
    def test_run_tests(self, mock_subprocess_run):
        mock_result = MagicMock()
        mock_result.stdout = b'Test output'
        mock_result.stderr = b''
        mock_result.returncode = 0
        mock_subprocess_run.return_value = mock_result

        test_runner = TestRunner()
        result = test_runner.run(test_directory='/path/to/tests')

        mock_subprocess_run.assert_called_once_with(
            'python -m unittest discover -s /path/to/tests', 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )

        self.assertEqual(result['stdout'], 'Test output')
        self.assertEqual(result['stderr'], '')

if __name__ == "__main__":
    unittest.main()
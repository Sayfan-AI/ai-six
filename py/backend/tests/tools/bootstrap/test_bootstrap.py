import unittest
from unittest.mock import patch
from py.backend.tools.bootstrap.bootstrap import Bootstrap
import os
import sys

class BootstrapToolTest(unittest.TestCase):

    @patch('os.execv')
    def test_bootstrap_execv_called(self, mock_execv):
        bootstrap_tool = Bootstrap()
        bootstrap_tool.run()
        mock_execv.assert_called_with(sys.executable, ['python'] + sys.argv)

if __name__ == "__main__":
    unittest.main()
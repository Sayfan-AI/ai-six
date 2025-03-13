import unittest
from unittest.mock import patch, MagicMock
from ..tools.file_system import ls
from ..tools.file_system.ls import Ls  # Adjust import path as needed


class LsToolTest(unittest.TestCase):

    @patch.object(ls, "sh")  # Adjust to actual import path of sh in your Ls module
    def test_run_ls_as_current_user(self, mock_sh):
        ls_tool = Ls(user=None)
        ls_tool.run(args="-l /tmp")
        mock_sh.ls.assert_called_with("-l", "/tmp")

    @patch.object (ls, "sh")  # Adjust to actual import path of sh in your Ls module
    def test_run_ls_as_different_user(self, mock_sh):
        ls_tool = Ls("other-user")
        ls_tool.run(args="-a /home")
        mock_sh.sudo.assert_called_with("-u", "other-user", "ls", "-a", "/home")


if __name__ == "__main__":
    unittest.main()
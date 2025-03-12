import unittest
from unittest.mock import patch, MagicMock
from ..tools.file_system import ls
from ..tools.file_system.ls import Ls  # Adjust import path as needed


class LsToolTest(unittest.TestCase):

    @patch.object(ls, "sh")  # Adjust to actual import path of sh in your Ls module
    def test_run_ls_as_current_user(self, mock_sh):
        # Create an instance of Ls with no user (defaults to current user)
        ls_tool = Ls(user=None)

        # Run with sample parameters
        ls_tool.run(["-l /tmp"])

        # Ensure sh.ls was called with correct args
        mock_sh.ls.assert_called_with("-l", "/tmp")

    @patch.object (ls, "sh")  # Adjust to actual import path of sh in your Ls module
    def test_run_ls_as_different_user(self, mock_sh):
        # Create an instance of Ls with a different user
        ls_tool = Ls(user="other-user")

        # Run with sample parameters
        ls_tool.run(["-a /home"])

        # Ensure sh.sudo is called with the user and correct args
        mock_sh.sudo.assert_called_with("ls", "-a", "/home", "-u", "other-user")


if __name__ == "__main__":
    unittest.main()
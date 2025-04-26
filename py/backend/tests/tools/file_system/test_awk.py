import unittest
from unittest.mock import patch
from py.backend.tools.file_system import awk
from py.backend.tools.file_system.awk import Awk


class AwkToolTest(unittest.TestCase):

    @patch.object(awk, "sh")
    def test_run_awk_as_current_user(self, mock_sh):
        awk_tool = Awk(user=None)
        awk_tool.run(args="/tmp/testfile.txt")
        mock_sh.awk.assert_called_with("/tmp/testfile.txt")

    @patch.object(awk, "sh")
    def test_run_awk_as_different_user(self, mock_sh):
        awk_tool = Awk("other-user")
        awk_tool.run(args="/home/other-user/testfile.txt")
        mock_sh.sudo.assert_called_with("-u", "other-user", "awk", "/home/other-user/testfile.txt")


if __name__ == "__main__":
    unittest.main()

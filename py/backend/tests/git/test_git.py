import unittest
from unittest.mock import patch, MagicMock
from py.backend.tools.git import git
from py.backend.tools.git.git import Git  # Adjust import path as needed


class GitToolTest(unittest.TestCase):

    @patch.object(git, "sh")
    def test_run_git_as_current_user(self, mock_sh):
        git_tool = Git(user=None)
        git_tool.run(args="status")
        mock_sh.git.assert_called_with("--no-pager", "status")

    @patch.object (git, "sh")
    def test_run_git_as_different_user(self, mock_sh):
        git_tool = Git("other-user")
        git_tool.run(args="pull")
        mock_sh.sudo.assert_called_with("-u", "other-user", "git", "--no-pager", "pull")


if __name__ == "__main__":
    unittest.main()
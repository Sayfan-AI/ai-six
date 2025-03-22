import unittest
from unittest.mock import patch

from py.backend.tools.kubectl import kubectl
from py.backend.tools.kubectl.kubectl import Kubectl

class TestKubectl(unittest.TestCase):

    def setUp(self):
        self.kubectl = Kubectl()

    def test_kubectl_initialization(self):
        # Test if Kubectl instance is created correctly
        self.assertIsInstance(self.kubectl, Kubectl)

    @patch.object(kubectl, "sh")
    def test_kubectl_run_method(self, mock_sh):
        kubectl_tool = Kubectl()
        kubectl_tool.run(args='get pods')
        mock_sh.kubectl.assert_called_with("get", "pods")

if __name__ == '__main__':
    unittest.main()
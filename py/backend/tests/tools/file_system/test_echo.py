import unittest
import os
import shutil
from py.backend.tools.file_system.echo import Echo


class EchoToolTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = "/tmp/echo_tool_test"
        self.test_file = os.path.join(self.test_dir, "test_file.txt")
        self.content = "Yeah, it works!!!"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_run_echo_creates_file_with_content_as_current_user(self):
        echo_tool = Echo()
        result = echo_tool.run(file_path=self.test_file, content=self.content)
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            file_content = f.read()
        self.assertEqual(file_content, self.content)
        self.assertEqual(result, f"Content written to {self.test_file}")

    @unittest.skip("Run manually with a valid username and sudo privileges")
    def test_run_echo_creates_file_with_content_as_other_user(self):
        other_user = "some-other-user"
        echo_tool = Echo(user=other_user)
        result = echo_tool.run(file_path=self.test_file, content=self.content)
        self.assertTrue(os.path.exists(self.test_file))
        with open(self.test_file, 'r') as f:
            file_content = f.read()
        self.assertEqual(file_content, self.content)
        self.assertEqual(result, f"Content written to {self.test_file} as user {other_user}")


if __name__ == "__main__":
    unittest.main()
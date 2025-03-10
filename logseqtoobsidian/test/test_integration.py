import os
import shutil
import subprocess
import unittest


class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.logseq_dir = "example/logseq_vault"
        self.output_dir = "example/obsidian_output"
        # Ensure the output directory is clean before each test
        if os.path.isdir(self.output_dir) and not os.path.islink(self.output_dir):
            shutil.rmtree(self.output_dir)
        elif os.path.exists(self.output_dir):
            os.remove(self.output_dir)

    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    def test_integration(self):
        result = subprocess.run(
            [
                "python",
                "-m",
                "logseqtoobsidian.__main__",
                "--logseq",
                self.logseq_dir,
                "--output",
                self.output_dir,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(self.output_dir))
        # Add more assertions as needed to verify the output


if __name__ == "__main__":
    unittest.main()

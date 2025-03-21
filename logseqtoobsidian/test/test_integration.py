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

    def exec(self, args):
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        return result

    def test_file_exists(self):
        result = self.exec([
                "python",
                "-m",
                "logseqtoobsidian.__main__",
                "--logseq",
                self.logseq_dir,
                "--output",
                self.output_dir,
            ])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "algorithms.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "contents.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "John 3.16.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "John 3.16-21.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "leetcode.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "Leetcode Title.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "links with colons.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "multiple tags in properties.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "algorithms", "attachments", "image_1688968010207_0.png")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "algorithms", "attachments", "image_1688968020649_0.png")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "algorithms", "dynamic programming", "memoization.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "algorithms", "dynamic programming.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "journals", "2023_08_03.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "journals", "2023_12_02.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "journals", "2023_12_03.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "journals", "attachments", "image_(1)_with_parentheses_1742412639003_0.png")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "journals", "attachments", "image.with.dots_1742414159033_0.png")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "leetcode", "BFS.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "leetcode", "dynamic programming.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "file", "with", "dots.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "hls__file__with__doubleunderscores__withoutspaces.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "hls__file_with_underscores.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "file_with_underscores.py")))

    def test_logseq_highlights_files_exist(self):
        result = self.exec([
                "python",
                "-m",
                "logseqtoobsidian.__main__",
                "--ignore_dot_for_namespaces",
                "--logseq",
                self.logseq_dir,
                "--output",
                self.output_dir,
            ])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "hls__file__with__doubleunderscores__withoutspaces.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "hls__file_with_underscores.md")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "file_with_underscores.py")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "file.with.dots.md")))

    def test_files_exists_with_assets_dir(self):
        result = self.exec([
                "python",
                "-m",
                "logseqtoobsidian.__main__",
                "--assets_dir",
                "assets",
                "--logseq",
                self.logseq_dir,
                "--output",
                self.output_dir,
            ])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "algorithms", "assets", "image_1688968010207_0.png")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "algorithms", "assets", "image_1688968020649_0.png")))


if __name__ == "__main__":
    unittest.main()

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.organize_chat_histories import OUTPUT_DIRECTORY, find_files, organize


class OrganizeChatHistoriesTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        (self.root / "first.md").write_text(
            "inseminationsklinik behandlung termin patientin beratung", encoding="utf-8"
        )
        (self.root / "second.md").write_text(
            "inseminationsklinik behandlung termin patientin beratung", encoding="utf-8"
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_preview_does_not_move_files(self):
        with redirect_stdout(io.StringIO()):
            organize(self.root, threshold=0.32, apply=False)

        self.assertTrue((self.root / "first.md").exists())
        self.assertFalse((self.root / OUTPUT_DIRECTORY).exists())

    def test_apply_can_be_cancelled(self):
        with patch("builtins.input", return_value=""), redirect_stdout(io.StringIO()) as output:
            organize(self.root, threshold=0.32, apply=True)

        self.assertIn("Cancelled", output.getvalue())
        self.assertTrue((self.root / "first.md").exists())

    def test_confirmed_apply_moves_files_and_ignores_output_on_rescan(self):
        with patch("builtins.input", return_value="JA"), redirect_stdout(io.StringIO()):
            organize(self.root, threshold=0.32, apply=True)

        output_root = self.root / OUTPUT_DIRECTORY
        self.assertEqual(2, len(list(output_root.rglob("*.md"))))
        self.assertEqual([], find_files(self.root))


if __name__ == "__main__":
    unittest.main()

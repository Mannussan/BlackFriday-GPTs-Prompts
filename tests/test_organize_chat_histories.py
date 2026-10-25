import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools.organize_chat_histories import OUTPUT_DIRECTORY, find_files, organize, load_document, make_group_name


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

        self.assertIn("Abgebrochen", output.getvalue())
        self.assertTrue((self.root / "first.md").exists())

    def test_confirmed_apply_moves_files_and_ignores_output_on_rescan(self):
        with patch("builtins.input", return_value="JA"), redirect_stdout(io.StringIO()):
            organize(self.root, threshold=0.32, apply=True)

        output_root = self.root / OUTPUT_DIRECTORY
        self.assertEqual(2, len(list(output_root.rglob("*.md"))))
        self.assertEqual([], find_files(self.root))

    def test_full_preview_precedes_confirmation_and_creates_nothing(self):
        with redirect_stdout(io.StringIO()) as output:
            def confirm(prompt):
                self.assertIn("VORSCHAU", output.getvalue())
                self.assertIn("first.md", output.getvalue())
                self.assertIn("second.md", output.getvalue())
                self.assertFalse((self.root / OUTPUT_DIRECTORY).exists())
                return ""
            with patch("builtins.input", side_effect=confirm):
                organize(self.root, threshold=0.32, apply=True)

    def test_only_exact_JA_is_accepted(self):
        for answer in ("ja", "Ja", "JA ", " JA", "J", "yes"):
            with self.subTest(answer=answer):
                with patch("builtins.input", return_value=answer), redirect_stdout(io.StringIO()):
                    organize(self.root, threshold=0.32, apply=True)
                self.assertTrue((self.root / "first.md").exists())
                self.assertFalse((self.root / OUTPUT_DIRECTORY).exists())

    def test_eof_and_keyboard_interrupt_cancel_before_moving(self):
        for error in (EOFError, KeyboardInterrupt):
            with self.subTest(error=error):
                with patch("builtins.input", side_effect=error), redirect_stdout(io.StringIO()):
                    organize(self.root, threshold=0.32, apply=True)
                self.assertTrue((self.root / "first.md").exists())
                self.assertFalse((self.root / OUTPUT_DIRECTORY).exists())

    def test_same_names_in_subdirectories_get_distinct_previewed_targets(self):
        nested = self.root / "Unterordner mit Leerzeichen"
        nested.mkdir()
        (nested / "first.md").write_text((self.root / "first.md").read_text(), encoding="utf-8")
        with patch("builtins.input", return_value="JA"), redirect_stdout(io.StringIO()) as output:
            organize(self.root, threshold=0.32, apply=True)
        self.assertIn("first_2.md", output.getvalue())
        self.assertEqual(3, len(list((self.root / OUTPUT_DIRECTORY).rglob("*.md"))))

    def test_existing_destination_is_preserved(self):
        group_name = make_group_name([load_document(self.root / "first.md"), load_document(self.root / "second.md")])
        folder = self.root / OUTPUT_DIRECTORY / group_name
        folder.mkdir(parents=True)
        (folder / "first.md").write_text("vorhandener Inhalt", encoding="utf-8")
        with patch("builtins.input", return_value="JA"), redirect_stdout(io.StringIO()):
            organize(self.root, threshold=0.32, apply=True)
        self.assertEqual("vorhandener Inhalt", (folder / "first.md").read_text(encoding="utf-8"))
        self.assertTrue((folder / "first_2.md").exists())

    def test_source_changed_during_confirmation_aborts_before_output_creation(self):
        def confirm(prompt):
            (self.root / "second.md").write_text("geaendert", encoding="utf-8")
            return "JA"
        with patch("builtins.input", side_effect=confirm), redirect_stdout(io.StringIO()):
            with self.assertRaises(OSError):
                organize(self.root, threshold=0.32, apply=True)
        self.assertTrue((self.root / "first.md").exists())
        self.assertFalse((self.root / OUTPUT_DIRECTORY).exists())

    def test_created_destination_after_preview_aborts_before_moving(self):
        group_name = make_group_name([load_document(self.root / "first.md"), load_document(self.root / "second.md")])
        folder = self.root / OUTPUT_DIRECTORY / group_name
        def confirm(prompt):
            folder.mkdir(parents=True)
            (folder / "first.md").write_text("neu erstellt", encoding="utf-8")
            return "JA"
        with patch("builtins.input", side_effect=confirm), redirect_stdout(io.StringIO()):
            with self.assertRaises(OSError):
                organize(self.root, threshold=0.32, apply=True)
        self.assertEqual("neu erstellt", (folder / "first.md").read_text(encoding="utf-8"))
        self.assertTrue((self.root / "first.md").exists())
        self.assertTrue((self.root / "second.md").exists())

    def test_technical_and_output_directories_are_excluded(self):
        for directory in (".git", ".venv", "node_modules", OUTPUT_DIRECTORY, OUTPUT_DIRECTORY.upper()):
            folder = self.root / directory
            folder.mkdir(exist_ok=True)
            (folder / "ignore.md").write_text("beispiel", encoding="utf-8")
        self.assertEqual(2, len(find_files(self.root)))

    def test_real_pdf_text_is_grouped_with_markdown(self):
        try:
            from pypdf import PdfWriter
            from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
        except ImportError:
            self.skipTest("Optionale PDF-Bibliothek nicht installiert")
        text = "gartenplanung pflanzen aussaat bewaesserung ernte kalender"
        writer = PdfWriter()
        page = writer.add_blank_page(width=595, height=842)
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                                 NameObject("/Subtype"): NameObject("/Type1"),
                                 NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"):
                                     DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 50 750 Td ({text}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
        writer.write(self.root / "garten.pdf")
        (self.root / "garten.md").write_text(text, encoding="utf-8")
        self.assertIn("gartenplanung", load_document(self.root / "garten.pdf").text)
        with patch("builtins.input", return_value="JA"), redirect_stdout(io.StringIO()):
            organize(self.root, threshold=0.32, apply=True)
        pdf_target, = (self.root / OUTPUT_DIRECTORY).rglob("garten.pdf")
        self.assertTrue((pdf_target.parent / "garten.md").exists())

    def test_empty_files_and_unrelated_documents_stay_in_place(self):
        (self.root / "empty.md").touch()
        (self.root / "unrelated.md").write_text("sternbilder weltraum astronomie satelliten beobachtung", encoding="utf-8")
        with patch("builtins.input", return_value="JA"), redirect_stdout(io.StringIO()):
            organize(self.root, threshold=0.32, apply=True)
        self.assertTrue((self.root / "empty.md").exists())
        self.assertTrue((self.root / "unrelated.md").exists())

    @unittest.skipUnless(os.name == "nt", "Windows-Starter")
    def test_windows_launcher_previews_and_cancels_with_spaces_in_path(self):
        launcher = Path(__file__).resolve().parents[1] / "Chatverlaeufe-sortieren.bat"
        result = subprocess.run(f'"{launcher}" "{self.root}"', shell=True, input="\n\n", capture_output=True,
                                encoding="utf-8", errors="replace", timeout=30,
                                env={**os.environ, "PYTHONUTF8": "1"})
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("VORSCHAU", result.stdout)
        self.assertIn("Abgebrochen", result.stdout)
        self.assertTrue((self.root / "first.md").exists())
        self.assertFalse((self.root / OUTPUT_DIRECTORY).exists())

    @unittest.skipUnless(os.name == "nt", "Windows-Starter")
    def test_windows_launcher_moves_only_after_JA(self):
        launcher = Path(__file__).resolve().parents[1] / "Chatverlaeufe-sortieren.bat"
        result = subprocess.run(f'"{launcher}" "{self.root}"', shell=True, input="JA\n\n", capture_output=True,
                                encoding="utf-8", errors="replace", timeout=30,
                                env={**os.environ, "PYTHONUTF8": "1"})
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("Fertig. 2 Dateien", result.stdout)
        self.assertEqual(2, len(list((self.root / OUTPUT_DIRECTORY).rglob("*.md"))))


if __name__ == "__main__":
    unittest.main()


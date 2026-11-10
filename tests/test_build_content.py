import subprocess
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from scripts import build_content
from scripts.content_blocks import ContentBlockError
from scripts.validate_profile import UniqueKeyLoader, validate_profile


class CompileCvTests(unittest.TestCase):
    def test_compile_cv_runs_texify_and_updates_public_pdf(self):
        root = MagicMock(spec=Path)
        cv_path = MagicMock(spec=Path)
        cv_path.name = "main.tex"
        cv_path.parent = Path("cv")
        cv_pdf_path = MagicMock(spec=Path)
        cv_pdf_path.is_file.return_value = True
        cv_pdf_path.stat.return_value.st_size = 100
        resume_path = MagicMock(spec=Path)
        resume_path.exists.return_value = False
        temporary = MagicMock(spec=Path)
        resume_path.with_suffix.return_value = temporary
        root.__truediv__.return_value = resume_path

        with (
            patch.object(build_content, "ROOT", root),
            patch.object(build_content, "CV_PATH", cv_path),
            patch.object(build_content, "CV_PDF_PATH", cv_pdf_path),
            patch("scripts.build_content.shutil.which", return_value="texify"),
            patch(
                "scripts.build_content.subprocess.run",
                return_value=subprocess.CompletedProcess([], 0),
            ) as run,
            patch("scripts.build_content.shutil.copyfile") as copyfile,
        ):
            result_path, changed = build_content.compile_cv("assets/resume.pdf")

        self.assertTrue(changed)
        self.assertIs(result_path, resume_path)
        command = run.call_args.args[0]
        self.assertEqual(command[0], "texify")
        self.assertIn("--pdf", command)
        self.assertNotIn("--clean", command)
        self.assertEqual(run.call_args.kwargs["cwd"], cv_path.parent)
        self.assertTrue(run.call_args.kwargs["check"])
        copyfile.assert_called_once_with(cv_pdf_path, temporary)
        temporary.replace.assert_called_once_with(resume_path)

    def test_compile_cv_requires_texify(self):
        with patch("scripts.build_content.shutil.which", return_value=None):
            with self.assertRaisesRegex(SystemExit, "texify was not found"):
                build_content.compile_cv("assets/resume.pdf")

    def test_compile_cv_rejects_resume_path_outside_root(self):
        with self.assertRaisesRegex(SystemExit, "inside the repository root"):
            build_content.compile_cv("../resume.pdf")

    def test_compile_cv_rejects_excess_pages(self):
        cv_pdf_path = MagicMock(spec=Path)
        cv_pdf_path.is_file.return_value = True
        cv_pdf_path.stat.return_value.st_size = 100
        with (
            patch.object(build_content, "CV_PDF_PATH", cv_pdf_path),
            patch("scripts.build_content.shutil.which", return_value="texify"),
            patch("scripts.build_content.subprocess.run"),
            patch("scripts.build_content.pdf_page_count", return_value=2),
        ):
            with self.assertRaisesRegex(SystemExit, "configured limit is 1"):
                build_content.compile_cv("assets/resume.pdf", page_limit=1)


class FullGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = build_content.load_profile()

    def test_cv_renders_every_targeted_section(self):
        rendered = build_content.render_cv(self.profile)
        self.assertIn(r"\section{Education}", rendered)
        self.assertIn(r"\section{Experience}", rendered)
        self.assertIn(r"\section{Projects}", rendered)
        self.assertIn(r"\section{Technical Skills}", rendered)
        self.assertIn("Fime", rendered)
        self.assertIn("Handwritten Text OCR", rendered)
        self.assertNotIn("Automatic Speech Recognition", rendered)

    def test_project_id_drives_generated_cv_anchor(self):
        profile = deepcopy(self.profile)
        project = next(record for record in profile["projects"] if record["id"] == "ocr")
        project["id"] = "handwritten-ocr"
        rendered = build_content.render_cv(profile)
        self.assertIn(r"portfolio/\#handwritten-ocr", rendered)
        self.assertNotIn(r"portfolio/\#ocr", rendered)

    def test_duplicate_ids_are_rejected(self):
        profile = deepcopy(self.profile)
        profile["projects"][1]["id"] = profile["projects"][0]["id"]
        with self.assertRaisesRegex(ContentBlockError, "duplicates"):
            validate_profile(profile)

    def test_duplicate_yaml_keys_are_rejected(self):
        with self.assertRaisesRegex(ContentBlockError, "duplicate key"):
            yaml.load("schema_version: 2\nschema_version: 2\n", Loader=UniqueKeyLoader)

    def test_resume_path_cannot_escape_repository_root(self):
        profile = deepcopy(self.profile)
        profile["settings"]["resume_filename"] = "../resume.pdf"
        with self.assertRaisesRegex(ContentBlockError, "inside the repository root"):
            validate_profile(profile)


if __name__ == "__main__":
    unittest.main()

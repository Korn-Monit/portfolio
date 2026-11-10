import unittest
from pathlib import Path
import re
import shutil

from scripts.package_site import package_site, validate_site


ROOT = Path(__file__).resolve().parents[1]


class PackageSiteTests(unittest.TestCase):
    def test_package_contains_only_deployable_site_files(self):
        output = ROOT / "scripts" / ".site-package-test"
        try:
            package_site(output)
            validate_site(output)

            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "generated" / "profile.js").is_file())
            self.assertTrue((output / "assets" / "resume.pdf").is_file())
            self.assertTrue((output / "assets" / "favicon.svg").is_file())
            self.assertTrue((output / "blog" / "index.html").is_file())
            self.assertTrue((output / ".nojekyll").is_file())
            self.assertFalse((output / "data" / "profile.yaml").exists())
            self.assertFalse((output / "scripts").exists())

            index_html = (output / "index.html").read_text(encoding="utf-8")
            resume_link = re.search(r'<a\b[^>]*\bid="resume-link"[^>]*>', index_html)
            self.assertIsNotNone(resume_link)
            resume_tag = resume_link.group(0)
            self.assertIn('href="assets/resume.pdf"', resume_tag)
            self.assertIn('target="_blank"', resume_tag)
            self.assertNotRegex(resume_tag, r"\bdownload(?:\s|=|>)")
        finally:
            if output.exists():
                shutil.rmtree(output)


if __name__ == "__main__":
    unittest.main()

import unittest

from scripts.content_blocks import ContentBlockError, render_latex_parts, validate_items


class ContentBlockTests(unittest.TestCase):
    def render(self, parts):
        validate_items([{"parts": parts}])
        return render_latex_parts(parts)

    def test_text_without_links(self):
        self.assertEqual(self.render([{"type": "text", "value": "Plain text"}]), "Plain text")

    def test_inline_link_and_text_after_it(self):
        result = self.render([
            {"type": "text", "value": "Read"},
            {"type": "link", "label": "the paper", "url": "https://example.com/paper"},
            {"type": "text", "value": "today"},
        ])
        self.assertEqual(result, r"Read \href{https://example.com/paper}{the paper} today")

    def test_link_after_break(self):
        result = self.render([
            {"type": "text", "value": "Details"},
            {"type": "break"},
            {"type": "link", "label": "Demo", "url": "https://example.com/demo"},
        ])
        self.assertEqual(result, r"Details \\\href{https://example.com/demo}{Demo}")

    def test_multiple_links_styles_and_no_join(self):
        result = self.render([
            {"type": "text", "value": "A", "styles": ["bold", "italic"]},
            {"type": "link", "label": "one", "url": "https://example.com/1"},
            {"type": "link", "label": ".", "url": "https://example.com/2", "join": "none"},
        ])
        self.assertEqual(result, r"\textbf{\textit{A}} \href{https://example.com/1}{one}\href{https://example.com/2}{.}")

    def test_destination_specific_parts(self):
        parts = [
            {"type": "text", "value": "Shared"},
            {"type": "text", "value": "CV", "targets": ["cv"]},
            {"type": "text", "value": "Web", "targets": ["portfolio"]},
        ]
        validate_items([{"parts": parts}])
        self.assertEqual(render_latex_parts(parts, "cv"), "Shared CV")
        self.assertEqual(render_latex_parts(parts, "portfolio"), "Shared Web")

    def test_invalid_url(self):
        with self.assertRaisesRegex(ContentBlockError, "must use http"):
            validate_items([{"parts": [{"type": "link", "label": "bad", "url": "javascript:alert(1)"}]}])

    def test_project_url_template(self):
        parts = [{
            "type": "link",
            "label": "demo",
            "url": "{portfolio_url}#{project_id}",
        }]
        context = {
            "portfolio_url": "https://example.com/portfolio/",
            "project_id": "new-project",
        }
        validate_items([{"parts": parts}], url_context=context)
        self.assertEqual(
            render_latex_parts(parts, url_context=context),
            r"\href{https://example.com/portfolio/\#new-project}{demo}",
        )

    def test_malformed_optional_fields(self):
        invalid_parts = [
            {"type": "text", "value": "x", "styles": ["underline"]},
            {"type": "text", "value": "x", "join": "tab"},
            {"type": "break", "value": "no"},
            {"type": "break", "join": "none"},
            {"type": "break", "targets": ["cv"]},
        ]
        for part in invalid_parts:
            with self.subTest(part=part), self.assertRaises(ContentBlockError):
                validate_items([{"parts": [part]}])


if __name__ == "__main__":
    unittest.main()

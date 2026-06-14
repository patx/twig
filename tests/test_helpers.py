import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("twig", ROOT / "twig.py")
twig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twig)


class HelperTests(unittest.TestCase):
    def test_detect_language_from_filename(self):
        self.assertEqual(twig.detect_language("example.py"), "python")
        self.assertEqual(twig.detect_language("index.html"), "html")
        self.assertEqual(twig.detect_language("style.css"), "css")
        self.assertEqual(twig.detect_language("script.js"), "javascript")
        self.assertEqual(twig.detect_language("README.md"), "markdown")
        self.assertEqual(twig.detect_language("Makefile"), "config")
        self.assertEqual(twig.detect_language("notes.txt"), "plain")

    def test_clamp_font_size(self):
        self.assertEqual(twig.clamp_font_size(1), twig.MIN_EDITOR_FONT_SIZE)
        self.assertEqual(twig.clamp_font_size(12), 12)
        self.assertEqual(twig.clamp_font_size(99), twig.MAX_EDITOR_FONT_SIZE)

    def test_line_count_for_text(self):
        self.assertEqual(twig.line_count_for_text(""), 1)
        self.assertEqual(twig.line_count_for_text("one"), 1)
        self.assertEqual(twig.line_count_for_text("one\ntwo"), 2)
        self.assertEqual(twig.line_count_for_text("one\n"), 2)

    def test_select_print_command_prefers_lpr_then_lp(self):
        self.assertEqual(twig.select_print_command(lambda command: command == "lpr"), "lpr")
        self.assertEqual(twig.select_print_command(lambda command: command == "lp"), "lp")
        self.assertIsNone(twig.select_print_command(lambda _command: None))


if __name__ == "__main__":
    unittest.main()

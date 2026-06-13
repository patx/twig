import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("twig", ROOT / "twig.py")
twig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(twig)


class EncodingTests(unittest.TestCase):
    def test_latin1_file_saves_as_utf8_when_text_needs_unicode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.txt"
            path.write_bytes("caf\xe9".encode("latin-1"))

            text, encoding = twig.read_text_file(path)
            self.assertEqual(text, "café")
            self.assertEqual(encoding, "latin-1")

            new_encoding = twig.write_text_file(path, text + " 🌿", encoding)

            self.assertEqual(new_encoding, "utf-8")
            self.assertEqual(path.read_text(encoding="utf-8"), "café 🌿")

    def test_latin1_file_keeps_latin1_when_possible(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.txt"
            path.write_bytes("caf\xe9".encode("latin-1"))

            text, encoding = twig.read_text_file(path)
            new_encoding = twig.write_text_file(path, text + "!", encoding)

            self.assertEqual(new_encoding, "latin-1")
            self.assertEqual(path.read_bytes(), "café!".encode("latin-1"))


if __name__ == "__main__":
    unittest.main()

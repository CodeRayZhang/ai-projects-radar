import tempfile
import unittest
from pathlib import Path
from build_index import entries, render

class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
    def article(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    def test_latest_count_missing_day_and_idempotency(self):
        self.article("2026-10/2026-10-18.md", "# Radar")
        self.article("2026-09/2026-09-25.md", "**1. [Actual | title]**")
        source = "Intro\n<!-- archive:start -->old duplicate rows<!-- archive:end -->\nFooter"
        result = render(self.root, source)
        self.assertIn("阅读 2026-10-18", result)
        self.assertIn("共 **2**", result)
        self.assertEqual(result.count("| [2026-09-25]"), 1)
        self.assertIn("Actual &#124; title", result)
        self.assertNotIn("2026-10-19", result)
        self.assertEqual(render(self.root, result), result)
        self.assertTrue(result.endswith("\nFooter"))
    def test_invalid_calendar_date(self):
        self.article("2026-02/2026-02-30.md", "# Invalid")
        with self.assertRaises(ValueError): entries(self.root)
    def test_wrong_month_directory(self):
        self.article("2026-09/2026-10-01.md", "# Invalid")
        with self.assertRaises(ValueError): entries(self.root)
    def test_empty_article(self):
        self.article("2026-10/2026-10-01.md", " ")
        with self.assertRaises(ValueError): entries(self.root)
    def test_missing_markers(self):
        with self.assertRaises(ValueError): render(self.root, "No markers")

if __name__ == "__main__": unittest.main()

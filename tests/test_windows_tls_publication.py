"""Negative regression checks for the published dataset validation logic."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_windows_tls_dataset import validate  # noqa: E402

DATA = ROOT / "docs/windows-tls-reality-check/v0.1/results.csv"


class DatasetValidationTests(unittest.TestCase):
    def setUp(self):
        with DATA.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.headers = reader.fieldnames
            self.rows = list(reader)

    def test_original_passes(self):
        self.assertEqual([], validate(DATA))

    def test_duplicate_run_rejected(self):
        self.rows.append(dict(self.rows[0]))
        self.assert_rejected()

    def test_wrong_tls_group_rejected(self):
        self.rows[0]["selected_groups"] = "29"
        self.assert_rejected()

    def test_bad_capture_digest_rejected(self):
        self.rows[0]["capture_sha256"] = "1234"
        self.assert_rejected()

    def test_missing_selected_run_rejected(self):
        self.rows.pop()
        self.assert_rejected()

    def test_false_http_success_rejected(self):
        target = next(x for x in self.rows if x["operator_result"] == "TLS_ERROR")
        target["operator_result"] = "HTTP200"
        self.assert_rejected()

    def assert_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.csv"
            with p.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writeheader()
                writer.writerows(self.rows)
            self.assertTrue(validate(p))


if __name__ == "__main__":
    unittest.main()

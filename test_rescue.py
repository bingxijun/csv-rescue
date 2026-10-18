"""Behavior tests. Fixtures are retained: this challenge never deletes files."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parent


class RescueTest(unittest.TestCase):
    def setUp(self):
        self.work = ROOT / "qa" / uuid.uuid4().hex
        self.work.mkdir(parents=True)
        self.source = self.work / "input.csv"
        self.config = self.work / "mapping.json"
        self.output = self.work / "result"
        self.source.write_text('Supplier SKU,Product Name,Price\n0007," Blue, mug ",0012.50\n0007,=2+2,0\n,Empty ID,9\n', encoding="utf-8-sig")
        self.rules = {"columns": {"sku": "Supplier SKU", "name": "Product Name", "price": "Price"}, "trim": ["name"], "required": ["sku"], "key": ["sku"]}
        self.save_rules()

    def save_rules(self):
        self.config.write_text(json.dumps(self.rules), encoding="utf-8")

    def run_cli(self):
        return subprocess.run([sys.executable, str(ROOT / "rescue.py"), str(self.source), "--config", str(self.config), "--output", str(self.output)], capture_output=True, text=True)

    def read_rows(self, name):
        with (self.output / name).open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.reader(handle))

    def test_preserves_ids_prices_source_and_all_rows(self):
        before = self.source.read_bytes()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = self.read_rows("data.csv")
        self.assertEqual(rows[1], ["0007", "Blue, mug", "0012.50"])
        self.assertEqual(len(rows), 4)
        self.assertEqual(self.source.read_bytes(), before)
        report = json.loads((self.output / "report.json").read_text())
        self.assertEqual(report["input_sha256"], hashlib.sha256(before).hexdigest())

    def test_flags_duplicate_and_missing_without_removing_rows(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((self.output / "report.json").read_text())
        self.assertEqual(report["rows_in"], 3)
        self.assertEqual(report["rows_out"], 3)
        self.assertEqual(report["duplicate_groups"], [{"records": [1, 2]}])
        self.assertEqual(report["missing_required"], [{"record": 3, "column": "sku"}])

    def test_spreadsheet_review_copy_neutralizes_formulas(self):
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertEqual(self.read_rows("data.csv")[2][1], "=2+2")
        self.assertEqual(self.read_rows("spreadsheet_review.csv")[2][1], "'=2+2")

    def test_rejects_existing_output_without_modifying_it(self):
        self.output.mkdir()
        marker = self.output / "marker.txt"
        marker.write_text("keep")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("output already exists", result.stderr)
        self.assertEqual(marker.read_text(), "keep")
        self.assertEqual(list(self.output.iterdir()), [marker])

    def test_rejects_ragged_rows(self):
        self.source.write_text("Supplier SKU,Product Name,Price\n0001,missing\n")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("record 1 has 2 fields; expected 3", result.stderr)
        self.assertFalse(self.output.exists())

    def test_rejects_unknown_source_column(self):
        self.rules["columns"]["sku"] = "absent"
        self.save_rules()
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown source column", result.stderr)
        self.assertFalse(self.output.exists())

    def test_supports_semicolon_and_multiline_quoted_text(self):
        self.source.write_text('Supplier SKU;Product Name;Price\n001;"a\nb";10.00\n', newline="")
        self.rules["delimiter"] = ";"
        self.save_rules()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read_rows("data.csv")[1], ["001", "a\nb", "10.00"])

    def test_duplicate_headers_are_rejected(self):
        self.source.write_text("Supplier SKU,Product Name,Product Name\na,b,c\n")
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate input headers", result.stderr)
        self.assertFalse(self.output.exists())

    def test_dangerous_headers_are_neutralized_in_review(self):
        self.rules["columns"]["=header"] = self.rules["columns"].pop("name")
        self.rules["trim"] = ["=header"]
        self.save_rules()
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertIn("'=header", self.read_rows("spreadsheet_review.csv")[0])


if __name__ == "__main__":
    unittest.main()

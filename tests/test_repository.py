import json
from pathlib import Path
import re
import unittest

from qdb_impact.model import percent

ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_reported_aggregate_arithmetic(self):
        data = json.loads((ROOT / "evidence/approved_project_metrics.json").read_text())
        self.assertEqual(percent(data["notes_marked_mapped"], data["unique_report_notes"]), data["reported_completion_percent"])
        self.assertEqual(percent(data["unique_rows_with_mapped_notes"], data["total_application_rows"]), data["reported_current_row_percent"])
        self.assertEqual(percent(data["potential_unique_rows_all_notes"], data["total_application_rows"]), data["reported_potential_row_percent"])
        self.assertEqual(data["potential_unique_rows_all_notes"] - data["unique_rows_with_mapped_notes"], 441157)
        self.assertIsNone(data["potential_cells_all_notes"])

    def test_relative_markdown_links_resolve(self):
        for path in ROOT.rglob("*.md"):
            if any(part in (".git", "outputs", "private") for part in path.parts):
                continue
            content = path.read_text(encoding="utf-8")
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
                if target.startswith(("http://", "https://", "#")):
                    continue
                target = target.split("#", 1)[0]
                with self.subTest(file=path.name, link=target):
                    self.assertTrue((path.parent / target).resolve().exists())

    def test_sql_has_no_company_source_identifiers(self):
        sql = (ROOT / "sql/10_impact_report.sql").read_text(encoding="utf-8")
        for forbidden in ("EMD_", "datawarehouse", "C:\\Users\\", "Standard_Motor_Products"):
            self.assertNotIn(forbidden, sql)
        aliases = re.findall(r"AS \[([^\]]+)\]", sql)
        self.assertTrue(all(len(a) <= 128 for a in aliases))

    def test_no_private_data_files_in_public_directories(self):
        forbidden_suffixes = {".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".mdf", ".ldf", ".bak"}
        for path in ROOT.rglob("*"):
            if any(part in (".git", "outputs", "private", ".venv") for part in path.parts):
                continue
            self.assertNotIn(path.suffix.lower(), forbidden_suffixes, str(path))


if __name__ == "__main__":
    unittest.main()

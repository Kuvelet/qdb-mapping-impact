"""Execute the actual final SELECTs with small SQLite dialect substitutions.

This verifies report joins/aggregation, not SQL Server execution, hashes or plans.
The optional tools/verify_sql_server.py covers the full T-SQL on a real engine.
"""

import copy
import json
from pathlib import Path
import re
import sqlite3
import unittest

from qdb_impact.model import SEARCH_COLUMNS, SUMMARY_HEADERS, analyze, clean

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "sql/10_impact_report.sql").read_text(encoding="utf-8")


def translate(query):
    query = query.replace("COUNT_BIG(", "COUNT(")
    return re.sub(r"#QdbImpact\w+", lambda m: '"' + m[0] + '"', query)


SUMMARY_SQL = translate(";WITH" + SQL.split("-- RESULT 1:", 1)[1].split(";WITH", 1)[1].split("-- RESULT 2:", 1)[0])
DETAIL_SQL = translate("SELECT" + SQL.split("-- RESULT 2:", 1)[1].split("\nSELECT", 1)[1].split("-- Release temporary storage.", 1)[0])

SCHEMA = '''
CREATE TABLE "#QdbImpactNotes" (NoteId INTEGER, NoteText TEXT, IsMapped INTEGER);
CREATE TABLE "#QdbImpactVio" (VioRowId INTEGER, Description TEXT);
CREATE TABLE "#QdbImpactCells" (NoteId INTEGER, VioRowId INTEGER, MatchColumn TEXT);
CREATE VIEW "#QdbImpactNoteRows" AS
    SELECT NoteId, VioRowId, COUNT(*) AS MatchedCellCount
    FROM "#QdbImpactCells" GROUP BY NoteId, VioRowId;
CREATE VIEW "#QdbImpactCoveredRows" AS
    SELECT r.VioRowId, SUM(r.MatchedCellCount) AS MappedCellCount
    FROM "#QdbImpactNoteRows" r JOIN "#QdbImpactNotes" n ON n.NoteId = r.NoteId
    WHERE n.IsMapped = 1 GROUP BY r.VioRowId;
CREATE VIEW "#QdbImpactDescriptions" AS
    SELECT ROW_NUMBER() OVER (ORDER BY Description) AS DescriptionId, Description
    FROM (SELECT DISTINCT Description FROM "#QdbImpactVio");
CREATE VIEW "#QdbImpactDescriptionPotential" AS
    SELECT v.Description, COUNT(*) AS PotentialCells
    FROM "#QdbImpactCells" c JOIN "#QdbImpactVio" v ON v.VioRowId = c.VioRowId
    GROUP BY v.Description;
CREATE VIEW "#QdbImpactNoteDescriptions" AS
    SELECT r.NoteId, v.Description, COUNT(*) AS MatchedVioRowCount
    FROM "#QdbImpactNoteRows" r JOIN "#QdbImpactVio" v ON v.VioRowId = r.VioRowId
    GROUP BY r.NoteId, v.Description;
CREATE VIEW "#QdbImpactNoteStats" AS
    SELECT NoteId, COUNT(*) AS DescriptionCount
    FROM "#QdbImpactNoteDescriptions" GROUP BY NoteId;
CREATE VIEW "#QdbImpactNoteDescriptionColumns" AS
    SELECT NoteId, Description, GROUP_CONCAT(MatchColumn, '; ') AS MatchedColumns
    FROM (
        SELECT DISTINCT c.NoteId, v.Description, c.MatchColumn
        FROM "#QdbImpactCells" c JOIN "#QdbImpactVio" v ON v.VioRowId = c.VioRowId
        ORDER BY c.MatchColumn
    ) GROUP BY NoteId, Description;
'''


def sql_report(data):
    with sqlite3.connect(":memory:") as db:
        db.row_factory = sqlite3.Row
        db.executescript(SCHEMA)
        notes = {clean(n["Note"]): (clean(n.get("MappingStatus")) or "").upper() == "MAPPED" for n in data["notes"]}
        note_ids = {n: i for i, n in enumerate(notes, 1)}
        db.executemany('INSERT INTO "#QdbImpactNotes" VALUES (?,?,?)', [(note_ids[n], n, mapped) for n, mapped in notes.items()])
        for row_id, application in enumerate(data["applications"], 1):
            db.execute('INSERT INTO "#QdbImpactVio" VALUES (?,?)', (row_id, clean(application.get("Description")) or None))
            for column in SEARCH_COLUMNS:
                value = clean(application.get(column))
                if value in notes:
                    db.execute('INSERT INTO "#QdbImpactCells" VALUES (?,?,?)', (note_ids[value], row_id, column))
        summary = dict(db.execute(SUMMARY_SQL).fetchone())
        for index in (3, 6, 9):
            key = SUMMARY_HEADERS[index]
            if summary[key] is not None:
                summary[key] = round(summary[key], 2)
        return {"summary": summary, "detail": [dict(r) for r in db.execute(DETAIL_SQL)]}


class SqlReportTests(unittest.TestCase):
    def test_sql_result_sets_match_reference(self):
        base = json.loads((ROOT / "examples/synthetic_catalog.json").read_text())
        cases = {"baseline": base}
        for status in ("Mapped", ""):
            data = copy.deepcopy(base)
            for note in data["notes"]:
                note["MappingStatus"] = status
            cases["status_" + status] = data
        for name, apps in (("empty", []), ("no_match", [{"Description": "Unmatched"}])):
            cases[name] = {"notes": base["notes"], "applications": apps}
        more = copy.deepcopy(base)
        more["applications"][0]["Color"] = "With auxiliary filter"
        cases["extra_cell_same_row"] = more
        duplicated = copy.deepcopy(base)
        duplicated["applications"].append(copy.deepcopy(base["applications"][0]))
        cases["duplicate_application"] = duplicated
        label = copy.deepcopy(base)
        label["applications"].append({"Description": "(No description)", "Note": "Two-port inlet"})
        cases["literal_null_label"] = label
        for name, data in cases.items():
            with self.subTest(case=name):
                actual = sql_report(data)
                expected = analyze(data["notes"], data["applications"])
                self.assertEqual(actual["summary"], expected["summary"])
                self.assertCountEqual(actual["detail"], expected["detail"])
                ranks = [r["This Description - Matching Cells If All Low Confidence QDB Report Notes Were Mapped"] for r in actual["detail"]]
                ranks = [r for r in ranks if r is not None]
                self.assertEqual(ranks, sorted(ranks, reverse=True))

    def test_sql_structure_preserves_matching_contract(self):
        searched = re.findall(r"\('([^']+)',\s+CONVERT\(nvarchar\(max\), a\.\[", SQL)
        self.assertEqual(searched, list(SEARCH_COLUMNS))
        self.assertIn("AND n.NoteText = c.CleanValue", SQL)
        self.assertIn("HASHBYTES('SHA2_256'", SQL)
        self.assertIn("Latin1_General_100_BIN2", SQL)
        self.assertNotIn("nvarchar(4000)", SQL)
        self.assertNotIn("NOLOCK", SQL)


if __name__ == "__main__":
    unittest.main()

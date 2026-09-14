import copy
import json
from pathlib import Path
import random
import unittest

from qdb_impact.model import DETAIL_HEADERS as D, SUMMARY_HEADERS as S, SEARCH_COLUMNS, analyze, clean

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return json.loads((ROOT / "examples/synthetic_catalog.json").read_text(encoding="utf-8"))


class MetricTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()

    def run_report(self):
        return analyze(self.data["notes"], self.data["applications"])

    def test_hand_calculated_summary(self):
        values = [6, 5, 3, 60.0, 5, 3, 50.0, 2, 4, 66.67, 3]
        self.assertEqual(self.run_report()["summary"], dict(zip(S, values)))

    def test_expected_artifact(self):
        expected = json.loads((ROOT / "examples/expected_report.json").read_text())
        self.assertEqual(self.run_report(), expected)

    def test_same_note_multiple_columns_counts_one_row(self):
        row = next(r for r in self.run_report()["detail"] if r[D[3]] == "With auxiliary filter")
        self.assertEqual(row[D[6]], 2)
        self.assertEqual(row[D[7]], "BodyStyle; Note")

    def test_overall_rows_cannot_be_summed_from_notes(self):
        report = self.run_report()
        per_note_total = sum(r[D[6]] or 0 for r in report["detail"] if r[D[4]] == "Mapped")
        self.assertEqual(per_note_total, 4)
        self.assertEqual(report["summary"][S[5]], 3)

    def test_priority_uses_all_cells_not_unique_rows(self):
        details = self.run_report()["detail"]
        values = {r[D[2]] for r in details if r[D[1]] == "Fuel Valve"}
        self.assertEqual(values, {5})
        priorities = [r[D[2]] for r in details if r[D[2]] is not None]
        self.assertEqual(priorities, sorted(priorities, reverse=True))

    def test_unmatched_notes_and_descriptions_are_retained(self):
        details = self.run_report()["detail"]
        self.assertEqual(len(details), 8)
        self.assertEqual(sum(r[D[0]] == "Note With No VIO Match" for r in details), 2)
        hose = next(r for r in details if r[D[1]] == "Service Hose")
        self.assertEqual(hose[D[2]], 0)
        self.assertIsNone(hose[D[3]])

    def test_position_is_excluded_and_lead_length_included(self):
        self.assertEqual(len(SEARCH_COLUMNS), 13)
        before = self.run_report()["summary"]
        self.data["applications"][-1]["Lead Length"] = "With auxiliary filter"
        after = self.run_report()["summary"]
        self.assertEqual(before[S[5]], 3)
        self.assertEqual(after[S[5]], 4)

    def test_duplicate_source_rows_are_separate_records(self):
        self.data["applications"].append(copy.deepcopy(self.data["applications"][1]))
        summary = self.run_report()["summary"]
        self.assertEqual(summary[S[0]], 7)
        self.assertEqual(summary[S[5]], 4)

    def test_null_description_is_counted(self):
        row = next(r for r in self.run_report()["detail"] if r[D[3]] == "Two-port inlet" and r[D[1]] is None)
        self.assertEqual(row[D[0]], "Note Found In Description")
        self.assertEqual(row[D[8]], 2)

    def test_literal_missing_label_is_not_null_group(self):
        self.data["applications"].append({"Description": "(No description)", "Note": "Two-port inlet"})
        self.assertEqual(self.run_report()["summary"][S[7]], 3)

    def test_completion_does_not_require_a_match(self):
        self.data["applications"] = [{"Description": "No overlap"}]
        summary = self.run_report()["summary"]
        self.assertEqual(summary[S[3]], 60)
        self.assertEqual(summary[S[5]], 0)

    def test_all_mapped_reaches_existing_potential(self):
        before = self.run_report()["summary"]
        for note in self.data["notes"]:
            note["MappingStatus"] = "Mapped"
        after = self.run_report()["summary"]
        self.assertEqual(after[S[3]], 100)
        self.assertEqual(after[S[5]], before[S[8]])
        self.assertEqual(after[S[8]], before[S[8]])

    def test_all_unmapped_keeps_potential(self):
        for note in self.data["notes"]:
            note["MappingStatus"] = ""
        summary = self.run_report()["summary"]
        self.assertEqual(summary[S[5]], 0)
        self.assertEqual(summary[S[8]], 4)

    def test_empty_applications_return_null_coverage_percent(self):
        self.data["applications"] = []
        result = self.run_report()
        self.assertEqual(len(result["detail"]), 5)
        self.assertIsNone(result["summary"][S[6]])
        self.assertIsNone(result["summary"][S[9]])

    def test_randomized_set_cardinality_invariants(self):
        rng = random.Random(913)
        for _ in range(100):
            notes = [{"Note": x, "MappingStatus": rng.choice(["", "Mapped"])} for x in "ABC"]
            apps = [{"Description": rng.choice(["X", "Y", None]), **{c: rng.choice(["A", "B", "C", "none", None]) for c in SEARCH_COLUMNS}}
                    for _ in range(rng.randint(0, 20))]
            report = analyze(notes, apps)
            summary = report["summary"]
            self.assertLessEqual(summary[S[5]], summary[S[8]])
            self.assertLessEqual(summary[S[8]], summary[S[0]])
            self.assertLessEqual(summary[S[5]], summary[S[4]])
            one_priority_per_description = {r[D[1]]: r[D[2]] for r in report["detail"] if r[D[2]] is not None}
            brute_force_cells = sum(v in {"A", "B", "C"} for a in apps for c, v in a.items() if c in SEARCH_COLUMNS and v is not None)
            self.assertEqual(sum(one_priority_per_description.values()), brute_force_cells)


class InputTests(unittest.TestCase):
    def test_empty_notes_rejected(self):
        with self.assertRaises(ValueError):
            analyze([], [])

    def test_blank_note_rejected(self):
        for text in (None, "", "   "):
            with self.subTest(text=text), self.assertRaises(ValueError):
                analyze([{"Note": text}], [])

    def test_unknown_status_rejected(self):
        with self.assertRaises(ValueError):
            analyze([{"Note": "A", "MappingStatus": "In progress"}], [])

    def test_conflicting_status_rejected(self):
        with self.assertRaises(ValueError):
            analyze([{"Note": "A", "MappingStatus": "Mapped"}, {"Note": " A "}], [])

    def test_duplicate_notes_deduplicated(self):
        report = analyze([{"Note": "A"}, {"Note": " A "}], [{"Note": "A"}])
        self.assertEqual(report["summary"][S[1]], 1)

    def test_status_case_and_spaces_normalized(self):
        report = analyze([{"Note": "A", "MappingStatus": " mapped "}], [])
        self.assertEqual(report["summary"][S[2]], 1)

    def test_note_case_and_accents_are_significant(self):
        report = analyze([{"Note": "Cafe", "MappingStatus": "Mapped"}], [{"Note": "cafe"}, {"Note": "Caf\u00e9"}, {"Note": " Cafe "}])
        self.assertEqual(report["summary"][S[5]], 1)

    def test_no_substring_matching(self):
        report = analyze([{"Note": "A"}], [{"Note": "prefix A suffix"}])
        self.assertEqual(report["summary"][S[8]], 0)

    def test_tabs_are_not_trimmed(self):
        self.assertEqual(clean(" \tA\t "), "\tA\t")
        report = analyze([{"Note": "A"}], [{"Note": "\tA\t"}])
        self.assertEqual(report["summary"][S[8]], 0)

    def test_long_values_are_not_truncated(self):
        note = "x" * 5000
        report = analyze([{"Note": note}], [{"Note": note}, {"Note": note + "y"}])
        self.assertEqual(report["summary"][S[8]], 1)

    def test_description_normalization(self):
        report = analyze([{"Note": "A"}], [{"Description": " X ", "Note": "A"}, {"Description": "X", "Note": "A"}, {"Description": " ", "Note": "A"}])
        self.assertEqual(report["summary"][S[10]], 2)

    def test_non_string_rejected(self):
        with self.assertRaises(ValueError):
            analyze([{"Note": "42"}], [{"Note": 42}])


if __name__ == "__main__":
    unittest.main()

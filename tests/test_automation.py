"""Offline checks only: no workbooks, Selenium install, browser, or PIM required."""

import csv
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
import importlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from automation import runtime


MODULES = {
    "no-parameter": "automation.automation_noparameter",
    "single-parameter": "automation.singleparameterauto",
    "dual-parameter": "automation.dualparameter",
}
ROOT = Path(__file__).resolve().parents[1]
ROW = {"Note": "Example note", "QDB Text": "Example qualifier",
       "Note Parameters": "25", "Note1 Parameter": "10", "Note2 Parameter": "20"}


class TemporaryWorkspace:
    # Use inherited directory permissions for synthetic fixtures in Windows sandboxes.
    def __init__(self):
        self.parent = (ROOT / "outputs" / "test-temp").resolve()
        self.path = self.parent / uuid4().hex
        self.path.mkdir(parents=True)
        self.name = str(self.path)

    def cleanup(self):
        resolved = self.path.resolve()
        if resolved.parent != self.parent or resolved == self.parent:
            raise ValueError("Test cleanup path escaped its output directory.")
        shutil.rmtree(resolved)

    def __enter__(self):
        return self.name

    def __exit__(self, *_):
        self.cleanup()


class Frame:
    def __init__(self, rows, indexes=None):
        self.rows = rows
        self.indexes = list(range(len(rows))) if indexes is None else indexes
        self.iloc = self

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, selection):
        return Frame(self.rows[selection], self.indexes[selection])

    def iterrows(self):
        return iter(zip(self.indexes, self.rows))


class FakeTimeout(Exception):
    pass


class Element:
    def __init__(self, driver, label):
        self.driver, self.label, self.text = driver, label, label

    def click(self):
        self.driver.clicks.append(self.label)

    def clear(self):
        pass

    def send_keys(self, value):
        self.driver.values.append((self.label, value))

    def is_displayed(self):
        return True


class Driver:
    def __init__(self, missing_result=None):
        self.clicks, self.values = [], []
        self.missing_result = missing_result
        self.result_lookups = 0
        self.get = Mock()
        self.quit = Mock()
        self.execute_script = Mock()

    def find_elements(self, *_):
        return [Element(self, "Parameter option 0"), Element(self, "Parameter option 1")]


class Wait:
    def __init__(self, driver, _timeout):
        self.driver = driver

    def until(self, condition):
        if callable(condition):
            return condition(self.driver)
        kind, locator = condition
        label = locator[1]
        if "normalize-space(text())='Example note'" in label:
            self.driver.result_lookups += 1
            if self.driver.result_lookups == self.driver.missing_result:
                raise FakeTimeout("Simulated missing result")
        if kind == "presence_of_all_elements_located":
            return [Element(self.driver, label)]
        if kind == "invisibility_of_element_located":
            return True
        return Element(self.driver, label)


def simulated_dependencies(driver):
    modules = {}

    def module(name, **attributes):
        item = ModuleType(name)
        item.__dict__.update(attributes)
        modules[name] = item
        if "." in name:
            parent, child = name.rsplit(".", 1)
            setattr(modules[parent], child, item)
        return item

    module("pandas", isna=lambda value: value is None)
    module("tqdm", tqdm=lambda rows, **_: rows)
    module("selenium")
    module("selenium.webdriver", Chrome=Mock(return_value=driver))
    module("selenium.common")
    module("selenium.common.exceptions", TimeoutException=FakeTimeout)
    module("selenium.webdriver.common")
    module("selenium.webdriver.common.by", By=SimpleNamespace(
        ID="id", XPATH="xpath", CSS_SELECTOR="css", CLASS_NAME="class"))
    module("selenium.webdriver.common.keys", Keys=SimpleNamespace(ENTER="ENTER", ESCAPE="ESCAPE"))
    module("selenium.webdriver.common.action_chains", ActionChains=Mock())
    module("selenium.webdriver.support")
    module("selenium.webdriver.support.ui", WebDriverWait=Wait)
    ec = module("selenium.webdriver.support.expected_conditions")
    for name in ("presence_of_all_elements_located", "presence_of_element_located",
                 "element_to_be_clickable", "visibility_of_element_located",
                 "invisibility_of_element_located"):
        setattr(ec, name, lambda locator, kind=name: (kind, locator))
    return modules


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryWorkspace()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "input.xlsx"
        # Only a CLI path fixture. It is never parsed as a workbook.
        self.path.touch()
        self.args = ["--input", str(self.path)]

    def parse(self, extra=(), mode="single-parameter"):
        return runtime.parse_settings(mode, self.args + list(extra))

    def test_defaults_are_bounded_preview(self):
        settings = self.parse()
        self.assertFalse(settings.execute)
        self.assertEqual((settings.start_row, settings.limit), (2, 1))
        self.assertIsNone(settings.url)

    def test_live_execution_requires_both_acknowledgement_and_url(self):
        for args in (["--execute"], ["--execute", "--allow-mapping-replacement"],
                     ["--execute", "--url", "https://example.invalid/Login"]):
            with self.subTest(args=args), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    self.parse(args)
        settings = self.parse(["--execute", "--allow-mapping-replacement", "--url",
                               "https://example.invalid/Login"])
        self.assertTrue(settings.execute)

    def test_http_requires_separate_acknowledgement(self):
        args = ["--execute", "--allow-mapping-replacement", "--url", "http://example.invalid/Login"]
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.parse(args)
        self.assertTrue(self.parse(args + ["--allow-insecure-http"]).execute)

    def test_invalid_bounds_and_urls(self):
        cases = [["--start-row", "1"], ["--limit", "0"], ["--limit", "-1"]]
        cases += [["--url", url] for url in (
            "file:///private", "https://name:secret@example.invalid", "https://example.invalid/?token=x",
            "https://example.invalid/#token", "https://", "not-a-url")]
        for args in cases:
            with self.subTest(args=args), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.parse(args)

    def test_missing_or_wrong_input_rejected(self):
        self.path.unlink()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.parse()
        wrong = self.path.with_suffix(".csv")
        wrong.touch()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            runtime.parse_settings("no-parameter", ["--input", str(wrong)])

    def test_header_contracts_and_duplicates(self):
        for mode, headers in runtime.REQUIRED_COLUMNS.items():
            with self.subTest(mode=mode):
                runtime.validate_headers(headers, mode)
                with self.assertRaises(ValueError):
                    runtime.validate_headers(headers[:-1], mode)
                with self.assertRaises(ValueError):
                    runtime.validate_headers(headers + ("Note",), mode)
        runtime.validate_headers(["Note", "QDB Text", "Note Parameters"], "no-parameter")

    def test_original_headers_checked_before_pandas_can_mangle_duplicates(self):
        raw = SimpleNamespace(iloc=[SimpleNamespace(tolist=lambda: ["Note", "QDB Text", "Note"])])
        class Raw:
            iloc = raw.iloc
            def __len__(self):
                return 1
        reader = Mock(return_value=Raw())
        with patch.dict(sys.modules, {"pandas": SimpleNamespace(read_excel=reader)}):
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                runtime.load_workbook(self.parse(mode="no-parameter"))
        reader.assert_called_once_with(self.path.resolve(), header=None, nrows=1)

    def test_selection_count(self):
        for total, start, limit, expected in [(10, 2, 1, 1), (10, 10, 10, 2),
                                              (10, 12, 10, 0), (0, 2, 1, 0)]:
            self.assertEqual(runtime.selected_row_count(total, start, limit), expected)

    def test_preview_cannot_create_run_paths(self):
        with self.assertRaises(ValueError):
            runtime.create_run_paths(self.parse())

    def test_live_run_paths_are_unique(self):
        settings = self.parse(["--execute", "--allow-mapping-replacement", "--url",
                               "https://example.invalid", "--output-dir", self.temp.name])
        first = runtime.create_run_paths(settings)
        second = runtime.create_run_paths(settings)
        self.assertNotEqual(first[0].parent, second[0].parent)
        self.assertTrue(first[0].parent.is_dir())


class WorkflowTests(unittest.TestCase):
    def test_import_and_help_need_no_optional_dependencies(self):
        for name in MODULES.values():
            with self.subTest(module=name):
                code = ("import importlib,sys; importlib.import_module(" + repr(name) + "); "
                        "assert not {'selenium','pandas','tqdm'} & set(sys.modules)")
                imported = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                                          capture_output=True, text=True, timeout=20)
                self.assertEqual(imported.returncode, 0, imported.stderr)
                self.assertEqual(imported.stdout, "")
                help_run = subprocess.run([sys.executable, "-m", name, "--help"], cwd=ROOT,
                                          capture_output=True, text=True, timeout=20)
                self.assertEqual(help_run.returncode, 0, help_run.stderr)
                self.assertIn("--allow-mapping-replacement", help_run.stdout)

    def test_pure_helpers(self):
        for mode, name in MODULES.items():
            m = importlib.import_module(name)
            self.assertEqual(m.format_elapsed_time(3661.9), "01:01:01")
            self.assertEqual(m.xpath_literal("plain"), "'plain'")
            self.assertEqual(m.xpath_literal("O'Neil"), '\"O\'Neil\"')
            self.assertEqual(m.xpath_literal('a\'b"c'), 'concat(\'a\', "\'", \'b"c\')')
            formatter = m.format_parameter_value if mode == "dual-parameter" else m.format_note_parameters
            self.assertEqual(formatter(datetime(2024, 2, 29)), "2/29/2024")
            self.assertEqual(formatter("0012"), "0012")
            self.assertEqual(formatter(12.5), "12.5")

    def run_workflow(self, mode, rows=None, missing_result=None, preview=False,
                     start=2, limit=1, interrupted=False):
        m = importlib.import_module(MODULES[mode])
        driver = Driver(missing_result)
        modules = simulated_dependencies(driver)
        rows = [dict(ROW)] if rows is None else rows
        with TemporaryWorkspace() as folder:
            path = Path(folder) / "input.xlsx"
            path.touch()
            args = ["--input", str(path), "--output-dir", str(Path(folder) / "outputs"),
                    "--start-row", str(start), "--limit", str(limit)]
            if not preview:
                args += ["--execute", "--allow-mapping-replacement", "--url", "https://example.invalid/Login"]
            with patch.dict(sys.modules, modules), patch.object(m, "load_workbook", return_value=Frame(rows)), \
                    patch.object(m.time, "sleep"), patch("builtins.input", return_value="",
                        side_effect=KeyboardInterrupt if interrupted else None), redirect_stdout(io.StringIO()) as out:
                if missing_result == 2:
                    with self.assertRaisesRegex(RuntimeError, "may already be removed"):
                        m.main(args)
                elif interrupted:
                    with self.assertRaises(KeyboardInterrupt):
                        m.main(args)
                elif not preview and runtime.selected_row_count(len(rows), start, limit) == 0:
                    with self.assertRaisesRegex(ValueError, "No input rows"):
                        m.main(args)
                else:
                    self.assertEqual(m.main(args), 0)
            reports = list(Path(folder).rglob("mapping_report.csv"))
            results = []
            for report in reports:
                with report.open(encoding="utf-8", newline="") as handle:
                    results.extend(csv.DictReader(handle))
            chrome_calls = modules["selenium.webdriver"].Chrome.call_count
            return driver, results, chrome_calls, out.getvalue()

    def test_preview_never_starts_chrome_or_creates_reports(self):
        for mode in MODULES:
            driver, rows, calls, output = self.run_workflow(mode, preview=True)
            self.assertEqual((rows, calls), ([], 0))
            driver.quit.assert_not_called()
            self.assertIn("No browser opened", output)

    def test_simulated_save_is_submitted_not_verified_success(self):
        for mode in MODULES:
            with self.subTest(mode=mode):
                driver, rows, calls, _ = self.run_workflow(mode)
                self.assertEqual(calls, 1)
                self.assertEqual([row["Status"] for row in rows], ["Submitted"])
                self.assertIn("not independently verified", rows[0]["Reason"])
                driver.quit.assert_called_once()
                actions = " ".join(driver.clicks)
                self.assertLess(actions.index("Remove Mapping"), actions.index("Add QDB"))
                values = [value for label, value in driver.values if label == "TextBoxACESTagQdbValue"]
                self.assertEqual(values, {"no-parameter": [], "single-parameter": ["25"],
                                          "dual-parameter": ["10", "20"]}[mode])
                if mode == "dual-parameter":
                    self.assertLess(driver.clicks.index("Parameter option 0"), driver.clicks.index("Parameter option 1"))

    def test_initial_missing_result_skips_without_removal(self):
        for mode in MODULES:
            driver, rows, _, _ = self.run_workflow(mode, missing_result=1)
            self.assertEqual(rows[0]["Status"], "Skipped")
            self.assertNotIn("Remove Mapping", " ".join(driver.clicks))
            driver.quit.assert_called_once()

    def test_disappearing_result_after_removal_stops_before_second_row(self):
        for mode in MODULES:
            driver, rows, _, _ = self.run_workflow(mode, rows=[dict(ROW), dict(ROW)],
                                                   missing_result=2, limit=2)
            self.assertEqual([row["Status"] for row in rows], ["Error"])
            self.assertIn("Remove Mapping", " ".join(driver.clicks))
            self.assertNotIn("Add QDB", " ".join(driver.clicks))
            driver.quit.assert_called_once()

    def test_missing_required_values_skip_before_mutation(self):
        for mode, required in runtime.REQUIRED_COLUMNS.items():
            for field in required:
                with self.subTest(mode=mode, field=field):
                    driver, rows, _, _ = self.run_workflow(mode, rows=[{**ROW, field: None}])
                    self.assertEqual(rows[0]["Status"], "Skipped")
                    self.assertEqual(driver.clicks, [])

    def test_start_row_and_limit_are_preserved_in_csv(self):
        for mode in MODULES:
            _, rows, _, _ = self.run_workflow(mode, rows=[dict(ROW)] * 3, start=3, limit=1)
            self.assertEqual([row["Excel Row"] for row in rows], ["3"])

    def test_empty_selection_does_not_launch_browser(self):
        for mode in MODULES:
            driver, rows, calls, _ = self.run_workflow(mode, rows=[])
            self.assertEqual((rows, calls), ([], 0))
            driver.quit.assert_not_called()

    def test_interrupt_after_launch_closes_browser(self):
        for mode in MODULES:
            driver, rows, _, _ = self.run_workflow(mode, interrupted=True)
            driver.quit.assert_called_once()
            self.assertEqual(rows, [])

    def test_no_private_endpoint_or_import_time_execution_in_adaptations(self):
        for name in MODULES.values():
            source = (ROOT / (name.replace(".", "/") + ".py")).read_text(encoding="utf-8")
            self.assertNotIn("smpcorp", source.lower())
            self.assertNotIn("C:\\Users\\", source)
            self.assertNotIn("3485", source)
            self.assertIn('if __name__ == "__main__":', source)


if __name__ == "__main__":
    unittest.main()

# Python Mapping Automation

## What It Automates

The three supplied scripts automate repetitive **PIM browser operations**, using Python, pandas, and Selenium. Each Excel row already contains a source note, a selected Qdb text, and any parameter values. The automation locates that note in the PIM grid, removes its existing mapping, adds the supplied Qdb selection, enters parameters when applicable, clicks Save, and records a row-level outcome.

This is **attended, spreadsheet-driven automation**, not automated mapping discovery. A person supplies the mapping decisions, logs in, navigates to the correct grid, supervises the batch, and reviews exceptions. The scripts do not perform fuzzy matching, machine learning, confidence scoring, Qdb API calls, or low-confidence export generation.

The business purpose is to reduce repeated interface work after a mapping decision has been made. SQL serves a different purpose: deciding where review effort has broad reuse and explaining the occurrence footprint of mapped notes. Neither layer replaces fitment expertise.

## Choose One Workflow

These are alternatives for different workbook schemas, not three consecutive pipeline steps. Excel row 1 contains headers; row 2 is the first data row. The first worksheet is read.

| Workflow | Source-derived script | Required Excel columns | Parameter behavior |
|---|---|---|---|
| No parameter | [automation_noparameter.py](../automation/automation_noparameter.py) | `Note`, `QDB Text` | Saves the selected qualifier without adding a parameter; optional `Note Parameters` is only logged |
| Single parameter | [singleparameterauto.py](../automation/singleparameterauto.py) | `Note`, `QDB Text`, `Note Parameters` | Chooses the first available parameter option and enters the supplied value |
| Dual parameter | [dualparameter.py](../automation/dualparameter.py) | `Note`, `QDB Text`, `Note1 Parameter`, `Note2 Parameter` | Selects visible option index 0, adds the first value, then reopens the dropdown and selects index 1 for the second |

For a synthetic illustration, a reviewed row might contain `Example note`, `Example qualifier with a value`, and parameter text `25`. These are invented labels, not licensed Qdb entries or recommended fitment mappings.

**Parameter meaning is not inferred or validated.** The dual workflow was supplied from a From/To workflow, but it uses dropdown positions rather than semantic labels. Verify both labels and their order after the first value is added. There is no unit conversion or range-order validation. Date-like values become M/D/YYYY; other values are stringified. Excel reading can infer types, so leading zeros and display formatting require particular care. Store meaningful text as text and review the values before execution. [pandas Excel reader](https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html).

## Source-Derived Execution Flow

1. Read the workbook and select an Excel-row range.
2. Open Chrome and pause for manual login and navigation to the Name filter.
3. Read the note, supplied Qdb text, and required parameter values. Missing values are logged and skipped.
4. Open the first grid filter, choose Text Filters > Equal, and enter the note.
5. Locate visible matching text. A missing initial result is skipped without requesting a mapping change.
6. Context-click the result and choose **Remove Mapping**.
7. Re-find and select the refreshed result, then choose Add QDB.
8. Search for the supplied Qdb text and select a matching dropdown entry.
9. Add zero, one, or two parameter values, then click Save and wait for the spinner to disappear.
10. Append a CSV outcome and elapsed-time log. Pause on an unexpected error; otherwise continue through the selected rows.

Removal and replacement are separate UI operations. A failure between them can leave a note unmapped or partly edited. The scripts do not capture the old mapping for rollback, and the application may not enforce the atomicity this workflow would need. Preserve an approved backup/export and a recovery procedure before any live batch.

## Technical Design

| Mechanism | Why it exists | Boundary |
|---|---|---|
| pandas workbook iteration | Turns reviewed mapping rows into repeatable actions | Reads the workbook into memory; not a streaming loader for the large raw TSV |
| Selenium explicit waits | Waits for visible, clickable, or no-spinner conditions | These are UI conditions, not a guarantee of persisted business state |
| Fresh element lookup after refresh | Avoids reusing the removed/refreshed grid element | The broad text locator is not a uniqueness check |
| XPath literal escaping | Supports text containing single and double quotes | XPath `normalize-space` is not the same normalization as the SQL report |
| Syncfusion `showPopup()` with click fallback | Opens the application's dropdown widget | Depends on its current DOM and JavaScript widget API |
| Limited menu/dropdown retries | Handles some transient UI timing failures | Does not make the whole replacement transaction retry-safe |
| Per-row CSV and text log | Records attempted input, status, reason, and timestamp | Contains private mapping content; not proof of deployment or an immutable audit store |

The no-parameter and single-parameter scripts retry exact-text Qdb dropdown selection up to three times and scope it to an open popup. The dual script retains a single inline selection whose final option locator is broader. The single-parameter script uses a JavaScript context-menu event; the other two use ActionChains. These differences are retained and documented rather than described as identical behavior.

The scripts combine explicit waits with fixed sleeps. A successful wait only establishes its specified condition; production validation should include the final mapping state. [Selenium waits](https://www.selenium.dev/documentation/webdriver/waits/).

## What Changed for This Repository

The original files were inspected without execution and remain unchanged in the owner's private folder. The same basenames are retained in `automation/`, but these are **adapted copies**, not byte-identical archival originals.

| Portfolio change | Reason |
|---|---|
| Explicit `main()` and delayed optional imports | Importing a module or requesting help does not launch Chrome, read a workbook, or write logs |
| Shared [runtime configuration](../automation/runtime.py) | Removes hard-coded private URL, input paths, and the single-script resume offset |
| Preview by default | Reads the supplied workbook and checks headers/range without browser activity |
| `--execute` plus `--allow-mapping-replacement` | Makes the destructive replacement behavior an explicit operator choice |
| Explicit URL; HTTPS preferred | No company endpoint or embedded credentials in the repo; legacy HTTP requires a separate acknowledgement |
| Default start row 2 and limit 1 | Makes the first authorized run a bounded pilot; larger batches require an explicit limit |
| Unique output folder per run | Preserves earlier logs instead of overwriting the previous run's fixed log |
| Stop if the result disappears after removal | The originals logged this case as Skipped and continued, although removal might already have occurred |
| `Submitted` instead of `Success` | Records the observed Save action without asserting persistence that the code does not verify |
| Browser cleanup in `finally` | Attempts to close Chrome on normal completion, exceptions, or interruption |

The core selectors, UI steps, parameter-selection behavior, waits, and retry differences remain source-derived. Broad result locators, first-column assumptions, and parameter order still require site-specific verification. The adaptations are not a claim that the private PIM workflow has been production-certified.

## Local Preview

Use Python 3.10+ from the repository root. Install optional dependencies in your chosen virtual environment:

```powershell
python -m pip install -r requirements-automation.txt
python -m automation.automation_noparameter --help
python -m automation.automation_noparameter --input 'C:\ApprovedInputs\mapping.xlsx' --limit 10
python -m automation.singleparameterauto --input 'C:\ApprovedInputs\single.xlsx' --limit 10
python -m automation.dualparameter --input 'C:\ApprovedInputs\from_to.xlsx' --limit 10
```

Only run the command for the workbook you actually have. These examples do not include workbook data. Preview checks required and duplicate headers, displays row counts and selection bounds, and performs no browser actions or report writes. It is not a row-by-row validation of mappings or a simulated PIM run. `--help` needs only the standard library; workbook preview needs pandas and openpyxl. Dependency ranges are portfolio setup constraints, not a recovered lockfile from the original environment.

## Authorized Browser Execution

Do not run against a production site merely to try the portfolio. First review the source, confirm permission, validate selectors and parameter ordering in a test environment, and establish a backup/recovery procedure. Review a single completed mapping in PIM before increasing the batch size.

```powershell
# Example placeholder URL: replace only with an explicitly authorized test endpoint.
python -m automation.singleparameterauto --input 'C:\ApprovedInputs\single.xlsx' --url 'https://authorized-pim.example/Login' --start-row 2 --limit 1 --execute --allow-mapping-replacement
```

For an approved legacy HTTP-only endpoint, `--allow-insecure-http` is additionally required; it acknowledges the lack of transport encryption, not a security fix. Login remains manual. Do not embed credentials in a URL or input file. `webdriver.Chrome()` can invoke Selenium Manager to locate or obtain browser-driver components, so live setup can require network access. [Selenium Manager](https://www.selenium.dev/documentation/selenium_manager/).

`--start-row` is a positional restart, not an idempotent resume. Do not replay a failed range until its actual PIM state has been reconciled. `--limit` includes skipped rows, not just submitted ones. The program pauses for login, on an unexpected error, and before closing at completion. Browser or process termination can leave incomplete logs and partially applied work.

## Read the Batch Results

Each live run creates `outputs/automation/<mode>_<timestamp>_<run-id>/` with `automation_log.txt` and `mapping_report.csv`. Keep these private, including when selecting a custom output location.

| CSV column | Meaning |
|---|---|
| Excel Row | Source worksheet row number, including the header offset |
| Note | Note requested by the workbook |
| QDB Text | Supplied target text, not a generated suggestion or verified qualifier ID |
| Note Parameters, or Note1 Parameter and Note2 Parameter | Values used or retained from that mode's input |
| Status | `Submitted`, `Skipped`, or `Error` in this adapted edition |
| Reason | Save-action message, skip reason, or exception details |
| Timestamp | Local wall-clock time of the report entry |

**Submitted** means the Save click and subsequent wait completed; no persisted mapping was read back. **Skipped** means a required value or initial result was missing before removal was requested. **Error** may occur before or after a mutation; inspect the actual record before proceeding. The original scripts used `Success` and `Mapped successfully` for the same unverified Save outcome and could use `Skipped` after removal. Do not merge original and adapted status semantics without review.

Logs can contain licensed text and business data. Treat spreadsheet cells as untrusted text when opening CSV output; use a controlled text import instead of allowing a spreadsheet application to interpret formula-like values. No credentials should be included in input rows or exception reports.

## Handoff to the SQL Tracker

```text
Reviewed Excel mapping instructions
  -> Python/Selenium attempts PIM changes
  -> Private batch CSV and PIM-state review
  -> Human-maintained unique-note MappingStatus list
  -> Validated manual SQL import + application snapshot
  -> Overall impact summary and note-by-description detail
```

The SQL input uses `Mapped` or blank. The Python CSV uses execution outcomes. **There is no automatic CSV-to-MappingStatus bridge in the supplied scripts or this repository.** Confirm the mapping in PIM before marking the note Mapped, reconcile incomplete/failed rows, and refresh the SQL status input manually. A batch submission does not prove the corresponding application rows were corrected or published downstream.

SQL then measures where those listed notes occur in 13 selected fields, including unmapped and unmatched items. Its exact matching is an analytics rule, not the automation's Qdb selection method. See the [metric dictionary](metrics.md) and [runbook](runbook.md).

## Verification and Next Hardening Steps

Offline tests check CLI guards, import safety, header contracts, pure formatting helpers, and simulated workflow control flow without opening a browser. They do not validate the live DOM, parameter semantics, Chrome/driver compatibility, persisted mappings, rollback, or throughput. No PIM execution was performed during repository preparation.

Before unattended operation, add stable record IDs and uniqueness checks, explicit parameter-label matching, pre-change state capture, post-save readback, failure reconciliation, and a versioned run manifest. A supported application API, if available and authorized, could replace fragile UI selectors. These are next steps, not capabilities claimed for the original implementation.

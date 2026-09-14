# Script Guide and Provenance

This page connects the code to the project workflow. It also separates surviving project work, historical commands, and new portfolio tooling so readers do not mistake a reconstruction for an original implementation.

**The project uses Python/Selenium for mapping execution and SQL for analysis.** Three source-derived PIM workflows are included in `automation/`; the separate `qdb_impact/` package demonstrates the SQL metrics. The workflow is attended, with a reviewed manual handoff between browser execution outcomes and the SQL mapping-status list.

## Start with the Mapping Workflows

| File | Role |
|---|---|
| [No parameter](../automation/automation_noparameter.py) | Apply supplied Qdb text without adding parameters |
| [Single parameter](../automation/singleparameterauto.py) | Apply supplied Qdb text and one value |
| [Dual parameter](../automation/dualparameter.py) | Apply supplied Qdb text and two values using dropdown option order |
| [Shared runtime](../automation/runtime.py) | Local preview, workbook header checks, explicit live-run controls, and output paths |
| [Optional dependencies](../requirements-automation.txt) | pandas/openpyxl for Excel; Selenium and tqdm for live execution |

Read the [Python automation guide](python-automation.md) before any execution. It describes input schemas, the Remove Mapping operation, original versus adapted behavior, and why a submitted Save is not persisted-state verification.

## Then Follow the Analysis

| Order | File | Input and output | Purpose |
|---|---|---|---|
| 1 | [Synthetic catalog](../examples/synthetic_catalog.json) | Invented notes, statuses, and application rows | Understand the example without a company extract |
| 2 | [Demo SQL inputs](../sql/00_demo_inputs.sql) | Synthetic records to two temporary input tables | Establish the input contract |
| 3 | [Impact report](../sql/10_impact_report.sql) | Notes + application inputs to two result sets | Follow validation, matching, deduplication, and reporting |
| 4 | [Reference model](../qdb_impact/model.py) | The same synthetic input to summary/detail dictionaries | Understand the counting rules through Python sets |
| 5 | [SQL regression tests](../tests/test_sql_reports.py) | Actual final SELECTs + small fixtures to assertions | Check the report's relational output logic |

For execution instructions, use the [runbook](runbook.md). For the motivation behind each stage, use the [project story](project-story.md).

## Original Work, Available and Missing

| Component | What is available | How it is represented here |
|---|---|---|
| Final working SQL report | The original `QDB_Mapped_Notes_Impact.sql` survives in the private working folder | Adapted into the portable SQL report; private source identifiers removed |
| Earlier counting-regression script | `test_impact_report.py` survives in the working folder | Its relational-check approach is carried into the public tests |
| TSV import work | bcp/PowerShell command history and a user-reported successful load | Sanitized command patterns below; original helper files and full destination schema are not recovered |
| Initial unique-note extraction | SQL shown in the project conversation | Documented as a reconstructed example, not an original saved script |
| Intermediate query revisions | Some SQL and error outputs in the conversation | Decision history, not a claim of a complete version archive |
| Original Python mapping scripts | All three supplied files inspected without execution | Adapted copies in `automation/`; original UI logic retained with documented preview, configuration, status, and stop/cleanup changes |
| Team progress email | Draft and local formatting artifact | Communication choices summarized in the project story; private draft not copied into the repo |

## Historical Ingestion Patterns

These snippets document the workflow using generic names. They are **not a verified import recipe for an unknown file**. Establish the real encoding, delimiter/quoting rules, column order, target types, and line endings before an import.

### Inspect Without Opening the Entire File

```powershell
$path = 'C:\ApprovedExports\example_lowconfidence.tsv'
Get-Item -LiteralPath $path | Select-Object Name, Length
Get-Content -LiteralPath $path -Encoding UTF8 -TotalCount 1
Get-Command bcp -ErrorAction SilentlyContinue
```

This example assumes UTF-8 for the header preview. It is a small read, not a scan for malformed rows, embedded newlines, or encoding errors. It does not establish the source's full schema.

### Bulk Load an Approved Raw Destination

The historical approach used Windows authentication, character input, UTF-8 code page, header skipping, and a batch size of 100,000. A parameterized example for an already-created, column-compatible destination is:

```powershell
# Example only: simple UTF-8 TSV with one header and Windows CRLF records.
# The -c defaults are tab-separated fields and CRLF row terminators.
bcp 'YOUR_DATABASE.dbo.YOUR_RAW_TABLE' in $path -S 'YOUR_SERVER\YOUR_INSTANCE' -T -c -C 65001 -F 2 -b 100000
```

The destination must already exist. `bcp in` inserts rows; it is not an idempotent replacement or a CSV-aware parser for arbitrary quoted multiline fields. Earlier batches may have committed before a failure. Inspect the destination and reconcile counts before a rerun; do not automatically delete or append to a partially loaded table. [Microsoft bcp documentation](https://learn.microsoft.com/en-us/sql/tools/bcp/bcp-utility?view=sql-server-ver17), [field and row terminators](https://learn.microsoft.com/en-us/sql/relational-databases/import-export/specify-field-and-row-terminators-sql-server?view=sql-server-ver17).

No import, installation, truncation, or connection to a company database is performed by the public demo.

### Derive the Review List

```sql
-- Reconstructed pattern. Creates a new table; it does not refresh an existing one.
SELECT DISTINCT CONVERT(nvarchar(max), [Note]) AS [Note]
INTO [dbo].[Example_UniqueNotes]
FROM [dbo].[Example_LowConfidence_Raw];
```

The raw table is retained. This initial-style extraction is not the same as final report validation: the impact query trims ordinary spaces, rejects blank notes, checks mapping statuses, and detects conflicting duplicate statuses. Do not confuse raw distinct values with the final validated note population.

## Original Sources and Portfolio Adaptations

The supplied original basenames are `automation_noparameter.py`, `singleparameterauto.py`, and `dualparameter.py`. They read Excel, open the private PIM site in Chrome, pause for manual login, apply supplied mappings, and write text logs and per-row CSV results. Private originals remain unchanged; their server URL and local configuration are not published.

The public copies preserve their individual UI workflows. The shared CLI, default preview, explicit replacement acknowledgement, bounded row selection, unique run folders, `Submitted` status, stop-after-removal behavior, and guaranteed browser-cleanup attempt were added for this edition. They are not claimed as features of the historical scripts.

The scripts do not generate the low-confidence export, infer target mappings, score candidates, or directly load SQL status. Their CSV outcomes need PIM-state review before updating the manually maintained `Mapped`/blank status list. No automatic bridge is implemented. [Complete source-derived behavior and adaptation table](python-automation.md).

## Portfolio Support Scripts

| File | What it does | Provenance |
|---|---|---|
| [Demo CLI](../qdb_impact/__main__.py) | Writes the synthetic report as JSON and Markdown | Added for the portfolio |
| [Demo builder](../tools/build_demo.py) | Generates SQL fixture and expected JSON from the synthetic catalog; supports `--check` | Added for the portfolio |
| [Chart builder](../tools/build_chart.py) | Renders the approved aggregate-results chart using Pillow | Added for the portfolio |
| [SQL Server checker](../tools/verify_sql_server.py) | Optionally executes the complete synthetic T-SQL against an explicitly authorized engine | Added for the portfolio; not yet run against SQL Server |
| [Automation tests](../tests/test_automation.py) | Checks import safety, execution guards, formatting, and simulated browser workflows | Added for the portfolio; no live PIM validation |
| [Metric tests](../tests/test_model.py) | Checks validation, overlap, boundary cases, and set invariants | Added for the portfolio |
| [Repository tests](../tests/test_repository.py) | Checks links, aggregate arithmetic, and basic data-leakage patterns | Added for the portfolio |
| [SQLCMD wrapper](../sql/run_demo.sql) | Runs synthetic input and report in one session | Added for the portfolio |
| [Private adapter template](../sql/private_adapter.sql.example) | Shows the two input contracts with generic source placeholders | Added for the portfolio; not an executable production adapter |

This inventory is intentionally explicit: the original mapping implementation should receive credit for its actual work, while demo infrastructure should not be presented as historical production tooling.

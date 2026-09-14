# Running and Adapting the Report

This page runs the impact-report demo and SQL analysis. For the three source-derived Selenium workflows, workbook schemas, preview commands, and explicit live-run controls, use the [Python automation guide](python-automation.md). For historical TSV ingestion and unique-note preparation, see the [script guide](scripts.md).

## Route 1: No Database Required

Use Python 3.10 or later from the repository root:

```bash
python -m qdb_impact
python -m unittest discover -s tests -v
python tools/build_demo.py --check
```

The reference demo reads `examples/synthetic_catalog.json` and generates Markdown and JSON under the ignored `outputs/` directory. Run it repeatedly without touching any database. For a different synthetic input, use `--input PATH --out-dir PATH`.

`tools/build_demo.py` regenerates the SQL fixture and expected JSON after an intentional fixture change. Review both diffs. The manually calculated test expectations must be updated independently when the scenario changes; do not accept generated expectations as proof of correctness by themselves.

## Route 2: SQL Server Synthetic Demo

Requirements: an authorized SQL Server 2017+ instance, database compatibility level 110+, and permission to connect and create local temporary tables. Use a sandbox database. No permanent tables, server settings, scheduled jobs, or company sources are changed by the demo.

In SSMS:

1. Connect to the sandbox and open a query window.
2. Run the entire `sql/00_demo_inputs.sql` file.
3. In the same query window/session, run the entire `sql/10_impact_report.sql` file.
4. Inspect the one-row summary and the eight-row synthetic detail result.

Or run from the repository root using Windows integrated authentication:

```bash
sqlcmd -S "YOUR_SERVER\YOUR_INSTANCE" -d "YOUR_SANDBOX_DATABASE" -E -b -i sql/run_demo.sql
```

The `:r` directives in `run_demo.sql` require sqlcmd or SSMS SQLCMD mode, with the repository root as the include-path working directory. For ordinary SSMS mode, use the two-file method instead. Do not weaken encryption or certificate validation to solve a connection error; use your organization's approved connection settings.

## Why the Same Session Matters

Names starting with `#` are session-local temporary tables. An input table created in one SSMS window is normally not available in another connection. Closing the connection removes it. The core releases its work tables on success; its two input tables remain available for a rerun until the session closes.

An `Invalid object name '#PortfolioNotes'` error normally means the input step did not run in this session, failed, or was run in a different query window. Re-run the complete input step, then the complete report. Selecting only the final SELECT also fails because its intermediate tables have not been built.

## Optional Full-Engine Verification

`tools/verify_sql_server.py` compares the complete SQL Server demo output against expected JSON. It requires the optional `pyodbc` Python package and a SQL Server ODBC driver. Supply an authorized connection string using the named environment variable; there is no default host or embedded credential.

Example for a Windows-authenticated sandbox with a valid server certificate:

```powershell
$env:QDB_SQL_CONNECTION_STRING = 'Driver={ODBC Driver 18 for SQL Server};Server=YOUR_SERVER\YOUR_INSTANCE;Database=YOUR_SANDBOX_DATABASE;Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=no;'
python tools/verify_sql_server.py
Remove-Item Env:\QDB_SQL_CONNECTION_STRING
```

This checker creates only synthetic temporary tables. It has not been executed during the portfolio build because no target SQL Server connection was supplied for that purpose. Its absence does not prevent running the Python demo or synthetic relational tests.

## Integrating Real Inputs

The included `sql/private_adapter.sql.example` is a non-runnable template until its private source placeholders are configured. Keep the working adapter under ignored `private/`, not in Git. Have the data owner review access, source scope, and data-sharing rules.

The adapter must supply the same two input tables and field names. Preserve original note text and formatting during import. Validate the manual CSV/table refresh before analysis: row count, required columns, empty-note checks, accepted statuses, and duplicate conflicts. If replacing a permanent mapping-status table, use a staging-and-validation workflow and an approved atomic replacement process rather than deleting the live table first.

The workflow updates SQL mapping status manually. There is no live Excel-to-SQL link or scheduled refresh. The SQL report does not write mappings; the separate Python automation can change PIM mappings in an explicitly enabled live run. Its batch outcome must be reviewed in PIM before manually marking a note Mapped.

For large datasets, avoid materializing the application source twice if an approved direct source integration is available. See [resource tradeoffs](architecture.md). Start with a representative sandbox population and measure execution plans, CPU, elapsed time, logical reads, memory grants/spills, tempdb consumption, and source blocking. No fixed runtime or index benefit is promised.

## Operating Checklist for Each Update

1. Confirm that the note list and application extract represent the intended business scope.
2. Validate imported mapping status and resolve duplicate conflicts.
3. Capture approved source versions and an as-of timestamp.
4. Run the complete report once using the agreed consistency strategy.
5. Check invariants from the metric dictionary and reconcile source row counts.
6. Review no-match notes and description-only exceptions.
7. Export both result sets into an approved private location.
8. Publish progress using distinct-note completion and distinct-row coverage separately.

For comparable updates, retain source snapshot identifiers, note-list version, searched-column set, query Git revision, execution timestamp, and validation result. The current query does not persist that history automatically. A future snapshot table should store those fields explicitly.

## Troubleshooting

| Symptom | What to investigate |
|---|---|
| Blank-note or unknown-status error | Input quality, extra whitespace, incorrect import columns |
| Conflicting-status error | The same cleaned note appears as both mapped and unmapped |
| More cells than unique rows | Expected when several matching cells share a row |
| Detail sums exceed overall row counts | Per-note rows overlap; use the overall union-based summary |
| Expected text has no match | Case, accents, surrounding tabs, excluded fields, longer cell text, or source-scope differences |
| Unexpectedly high application counts | Duplicates or joins in the source view; report IDs preserve every source output row |
| Slow execution | Source-view plan, resource contention, spills, tempdb capacity, concurrent runs, or a changed data distribution |

Do not infer an estimated finish time from how quickly result rows arrive. Query stages can have very different costs, and some aggregates return output only after substantial upstream work.

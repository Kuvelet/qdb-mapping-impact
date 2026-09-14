# Technical Architecture: Automation and Analysis

## Design Goal

Connect Python mapping automation to explainable SQL analysis of a note backlog and a much larger application dataset. The SQL reporting layer reads catalog records and measures impact; it does not modify those source records. The Python execution layer is intentionally different: an authorized live run removes and replaces PIM mappings.

The original operating workflow includes Python mapping scripts, raw-file ingestion, note-list preparation, and SQL impact analysis. The project owner confirms the Python/SQL division of responsibility. The [project story](project-story.md) covers the available development history; the [script guide](scripts.md) records source availability.

## System Layers

| Layer | Role | Implementation evidence |
|---|---|---|
| Source-derived Python automation | Applies Excel-supplied mapping decisions in the PIM browser UI | Three inspected Selenium scripts, adapted with shared execution controls; zero/one/two-parameter workflows |
| Data exchange and preparation | Makes raw exports, unique notes, and mapping status available to SQL | Import commands and manually refreshed status workflow documented |
| SQL analytics | Measures occurrences, unique-row coverage, description priorities, and progress | Report source available and adapted in this repository |
| Portfolio verification | Explains and tests the report with synthetic records | New `qdb_impact/` reference model and tests; not the original mapping engine |

## Python Execution Boundary

`automation/runtime.py` parses configuration and validates workbook headers before optional browser imports. Each workflow then performs its original site-specific UI steps using Selenium. The default preview returns before browser initialization or log creation; live execution requires an explicit URL and replacement acknowledgement.

The workflows apply supplied decisions rather than discover them. A row's execution outcome is appended to a private CSV; the target mapping is not read back. Manual PIM-state review and status reconciliation connect this stage to SQL. There is no shared transaction or automatic synchronization between the browser operation and reporting inputs.

The [Python guide](python-automation.md) covers selectors, parameter ordering, retries, failure modes, and source adaptations. The remaining sections detail the SQL analytics implementation.

The impact report reads a manually refreshed mapping-status table. The public repository separates that report logic from company infrastructure by exposing temporary input tables and supplying synthetic records.

## SQL Input Contract

`#PortfolioNotes` supplies `[Note]` and `[MappingStatus]`. Each note is a candidate for review; its status is `Mapped` or blank/NULL. Exact duplicate note/status pairs are deduplicated. Blank notes, unknown statuses, conflicting duplicate statuses, and an empty note input are rejected before processing application matches.

`#PortfolioApplications` supplies `[Description]` and these 13 searched fields:

```text
BodyStyle, BrakeType, CarbNumber, CarbType, Color, Connection Type,
Cylinder Head Type, Emissions, FootNote, Lead Length, Note,
OE Number, Split Year
```

Position is deliberately excluded. Any `MatchingColumns` value in the original mapping spreadsheet is informational and does not constrain matching. Values are interpreted as text after source conversion, so the adapter must preserve any meaningful formatting, such as leading zeros in identifiers.

## Processing Stages and Grains

| Stage | Grain | Reason for materializing it |
|---|---|---|
| Validated notes | One cleaned note | Ensure duplicates do not inflate counts |
| Application snapshot | One source-view output row | Assign a row identity before expanding fields |
| Matched cells | Note ID + application row ID + column | Preserve occurrence counts and field lineage |
| Note rows | Note ID + application row ID | Collapse the same note appearing in several fields |
| Covered rows | Application row ID for mapped notes | Collapse overlap across different mapped notes |
| Description potential | Description | Rank descriptions using all matching cells |
| Note-description detail | Note ID + description | Explain where each note appears |
| Overall summary | One report run | Show progress, current reach, and full-list potential |

Rows receive `IDENTITY(bigint, 1, 1)` before `CROSS APPLY` expands the fields. This identifier represents a record in this run. It is not a permanent application key and cannot be compared across refreshes. Identical source rows receive distinct IDs; the report does not remove source-view duplicates or deduplicate underlying vehicles.

## Matching Contract

1. Convert note and candidate cell text to `nvarchar(max)`.
2. Trim ordinary leading/trailing spaces with `LTRIM/RTRIM`.
3. Compare complete values, with case and accents significant.
4. Use SHA2-256 hashes as narrow join keys, then verify full text equality.

This is not substring, token, fuzzy, spelling, unit-conversion, or semantic matching. Tabs, newlines, non-breaking spaces, abbreviations, and Unicode normalization differences are not silently repaired. A conservative occurrence detector can miss related wording; it must not be advertised as a semantic mapping engine.

Hash equality is not sufficient by itself. The full text predicate remains in the join so a hash collision cannot create a false match. Binary comparison keeps the text comparison consistent with hashing of Unicode input. The public version normalizes descriptions by trimming ordinary spaces, converting blank descriptions to NULL, and using `Latin1_General_100_BIN2` for grouping.

`CROSS APPLY (VALUES ...)` expresses the same set of candidate fields for each application row. This expands each row into up to 13 logical candidates; only exact matches to the note list are stored in the matched-cell table. It still requires inspecting the chosen fields. [Microsoft APPLY documentation](https://learn.microsoft.com/en-us/sql/t-sql/queries/from-transact-sql?view=sql-server-ver17).

## Why Temporary Tables and Hashes?

The query evolved after an early approach was reported to run for more than an hour. The subsequent staged approach was reported as much faster, but no controlled runtime benchmark was captured. The defensible claim is an architectural improvement with qualitative user feedback, not a quantified speedup.

Temporary tables make the intermediate grains explicit, permit indexes, and avoid repeatedly rebuilding the same matching relations for different report sections. Hash keys avoid indexing very long note strings. SHA2-256 returns a fixed 32-byte value. This addresses the long-index-key issue encountered during development. [Microsoft HASHBYTES](https://learn.microsoft.com/en-us/sql/t-sql/functions/hashbytes-transact-sql?view=sql-server-ver17).

`nvarchar(max)` prevents the deliberate 4,000-character truncation imposed by the earlier prototype. The same large-object type is used inside `STRING_AGG` so long aggregated field lists are not constrained by the smaller fixed-width aggregation return types. The column list is deduplicated before aggregation. [Microsoft STRING_AGG](https://learn.microsoft.com/en-us/sql/t-sql/functions/string-agg-transact-sql?view=sql-server-ver17).

`COUNT_BIG` and bigint row IDs support large populations. Separate note-row and overall-row stages make double-count prevention visible in the code, rather than relying on consumers to compensate in Excel.

## Resource and Consistency Tradeoffs

Hashing millions of values consumes CPU. `nvarchar(max)` and materialized snapshots use memory and tempdb space. Sorts, hash joins, index creation, and string aggregation can spill or contend with other workloads. No SQL design guarantees a fixed duration on an unknown server.

The demo input adapter materializes input tables and the core creates its own application snapshot. That is convenient for reproducibility but adds a copy. A production integration can use approved source views directly in the two source SELECTs and adjust the preflight checks, avoiding the extra adapter copy. Measure the resulting plan and tempdb use before scheduling large runs.

The core's temporary snapshot is a stored input set for the remainder of the calculation. It does **not** by itself guarantee a transactionally consistent cross-source capture. For an auditable as-of report, coordinate an immutable extract or DBA-approved snapshot/isolation strategy across the note and application inputs. Do not use `NOLOCK` to disguise blocking at the cost of unreliable counts. [Microsoft isolation-level documentation](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql?view=sql-server-ver17).

## Public Edition Differences

The working company query outside this repository is unchanged. The portfolio edition substitutes generic temporary inputs, normalizes descriptions explicitly, and leaves missing descriptions as SQL NULL instead of replacing them with a display string. A real description named `(No description)` therefore cannot be visually confused with the NULL group in machine-readable output. The `Report Row Type` still distinguishes a matched missing-description group from a note with no match anywhere.

The Python reference implementation is deliberately small and dependency-free. It uses sets to make the metric definitions executable. It does not reproduce SQL Server plans, collation ordering for every Unicode value, locking, or performance. It is for learning, fixtures, and regression checks, not millions-of-rows production ETL.

## Validation Layers

1. Hand-calculated synthetic counts and edge-case tests validate the reference metric contract.
2. Tests extract the actual final summary and detail SELECTs from the SQL file and run their relational logic in SQLite with narrow dialect substitutions.
3. An optional pyodbc checker runs the complete synthetic T-SQL on an explicitly supplied SQL Server and compares both result sets with expected JSON.
4. Real deployment requires engine testing, source reconciliation, permissions review, and performance measurement in the target environment.

The first two layers were run locally for this portfolio build. The optional real SQL Server check has not been run as part of that build. CI repeats synthetic tests, not company-data validation.

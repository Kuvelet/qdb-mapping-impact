# The Project Story: Python Mapping Automation and SQL Analysis

## The Original Motivation

The project combines two responsibilities: **perform mapping work with Python scripts, then use SQL to understand the results and their catalog impact.** Automation is the execution layer; analysis explains progress, exceptions, priorities, and application reach.

Within that larger project, the SQL discussion began with a practical question: what are the distinct low-confidence notes, and where do they occur in the application catalog? A raw report contains repeated records. A reviewer needs a manageable list of decisions, while the business needs to understand their reach.

Those are different levels of the same problem. A note is a review item; its repeated use represents workload and potential reuse; an application row is a record that may be reached by several notes. The project gradually connected those levels instead of treating every count as the same thing.

The source now includes three original Python workflows supplied by the project owner: no-parameter, single-parameter, and dual-parameter mapping. Inspection establishes that they use Excel instructions and Selenium to apply preselected mappings in PIM. The conversation and SQL source document the analysis, ingestion troubleshooting, report iterations, and stakeholder communication. Exact historical run dates and full production execution logs are not available.

## The Work in One View

| Stage | Question we needed to answer | Work and reasoning |
|---|---|---|
| Automate mapping | How can reviewed mapping decisions be applied repeatedly? | Read Excel instructions and use Selenium to apply zero-, one-, or two-parameter mappings through the PIM UI |
| Discover | What notes are we dealing with? | Extract distinct Note values from an existing raw SQL table |
| Contextualize | Where does each note appear? | Search selected application fields; keep the field name and product description |
| Make execution practical | Can we run this analysis reliably at the available scale? | Stage results, fix long-text issues, and use indexed hash-assisted matching |
| Extend the input workflow | How do we handle another export too large to inspect interactively? | Use PowerShell and bcp to load the TSV, then create a unique-note table |
| Connect mapping work | Which unique notes have been mapped? | Bring mapping status from the working spreadsheet/CSV into SQL |
| Validate the numbers | What counts as an occurrence or an affected application? | Separate cells, note-row pairs, unique rows, and description groups |
| Prioritize | Which description cluster should reviewers work on first? | Rank descriptions by all-list matching-cell counts with stakeholder input |
| Communicate | Can another person understand progress without decoding the query? | Separate a compact overall summary from traceable note-by-description detail |

This groups the project's responsibilities; it is not a verified chronological sequence for the Python pipeline. The detailed sequence below follows the SQL discussion available in the conversation. In particular, that first SQL analysis preceded the later large-file import discussion. Calendar dates and benchmark durations are not invented where the source record is incomplete.

## The Python Work: Turn Mapping Decisions into Repeatable Actions

Making a mapping decision and entering it into PIM are different kinds of work. A reviewer needs to establish which qualifier and values preserve the note's meaning. Once supplied in Excel, the repeated interface steps can be automated: locate the note, remove its old mapping, select the supplied Qdb text, enter parameters, and save.

The three scripts represent the practical variation in those instructions. Some mappings require no value entry; others require one value; From/To-style work supplies two. Separate workflows retain those differences. pandas reads the workbook, Selenium drives the grid and dialogs, and per-row CSV results and elapsed-time logs help the operator follow the batch.

Dynamic UI behavior introduced additional engineering work: explicit waits for loading and clickability, fresh lookups after grid refresh, quote-safe XPath construction, dropdown opening through the widget instance, and limited retries around some menus. These are site-specific controls, not a guarantee that the UI cannot change.

The original scripts pause for login and exceptions. They do not choose mappings, validate semantic equivalence, or read back persisted changes. Their Remove Mapping step also makes failures significant: replacement is not one atomic operation. The portfolio copies expose this boundary with preview defaults and explicit run acknowledgement, stop if the row disappears after removal, and label completed Save actions `Submitted` rather than verified success.

This makes the project's division of labor concrete: **a person provides and verifies the mapping decision, Python repeats the application steps, and SQL explains the scope and progress.** [Full workflow and source adaptations](python-automation.md).

## 1. Begin the SQL Analysis with Distinct Notes

The first SQL question was a distinct-value query on the raw report's Note column. Conceptually:

```sql
SELECT DISTINCT [Note]
FROM [dbo].[Example_LowConfidence_Raw];
```

The next step was to make those unique values available as a table for repeated analysis. This established a reusable review population: a note that appears many times in the raw export should not automatically become many separate mapping tasks.

The important design choice was retaining the raw source separately. Raw records preserve occurrence context; the unique-note table provides the backlog. Later, the final tracker added explicit trimming and duplicate-status validation. Those later rules should not be silently attributed to the first exploratory query.

## 2. Discover That Note Text Is Not Confined to the Note Field

The application source was a view in another database on the same SQL Server. We wanted to find exact matches not only in Note, but in fields such as CarbType, FootNote, BodyStyle, and others.

The requirement was refined from "how many matches does a note have?" to **"how many matches does it have in each searched column?"** Keeping the column name matters: it shows where text is stored and gives a reviewer more useful context than a single total.

The discussion compared cross joins with a `CROSS APPLY (VALUES ...)` representation. The selected approach exposes the searched fields as `(MatchColumn, MatchValue)` candidates for each application row. The matching condition then connects those candidates to the unique-note list. It is an occurrence search, not a decision about which Qdb qualifier should represent the text.

Position was initially included. Lead Length was added later, and Position was subsequently removed at the project owner's request. The final report searches 13 fields. [Exact current field set](architecture.md).

## 3. Keep Exceptions and Add Product Context

A report containing only successful matches could make the backlog appear smaller than it was. We changed the logic so every searched note remained visible, even with no matches.

We then added matching descriptions. Early outputs combined distinct description values with a semicolon delimiter to avoid long repeated strings. Another requested measure counted how many different searched columns matched a note.

As the business question shifted toward product-description prioritization, the report shape changed again: descriptions became a grouping dimension, and each note received its own detail row. Some earlier aggregate columns were useful during exploration but were not retained in the simplified final report.

That evolution is deliberate. The final report is not supposed to display every metric ever discussed; it should expose the metrics that support the current decision and preserve enough detail to investigate them.

## 4. Work Through Query Execution and Long-Text Problems

An early query was reported to still be running after more than an hour. The discussion considered whether incoming result-row counts could indicate remaining time and whether concurrent queries might add server contention. We did not establish a reliable ETA or a controlled performance benchmark.

One temporary compromise was to aggregate matching descriptions only when the matched column was Position. After a later query ran much faster according to the project owner, description aggregation was expanded to other fields again. The final design eventually organized description detail directly rather than building one large description string per note.

The iterations exposed concrete implementation issues:

| Issue encountered | What it taught us | Design response represented in the surviving code |
|---|---|---|
| Long-running matching and aggregation | Repeated large operations needed to be made visible and reusable | Materialize application and match stages, then aggregate from those stages |
| Nonclustered-index key-length warnings | Long note text is an unsuitable narrow index key | Use fixed-width SHA2-256 keys and keep exact text verification |
| STRING_AGG exceeded its result-size limit | Aggregation return types matter for large text | Convert aggregation inputs to `nvarchar(max)` |
| Missing hash-column errors during iterations | A partial or inconsistent script is difficult to rerun reliably | Keep table definitions and consumers together in a complete report script |
| Invalid temporary-table object names | Session scope and execution order are part of the workflow | Run preparation and reporting in the same connection |

The error messages do not establish a single root cause for every failed historical run; the full earlier revisions are not all available. The public code contains the later staged design, not a fabricated archive of those revisions.

Messages such as "rows affected" during these runs often described rows inserted into temporary tables. They were not a report of catalog corrections. Likewise, intermediate expanded-match counts were not interchangeable with source application-row counts.

## 5. Extend the Workflow to a Large TSV Export

Later, another low-confidence TSV was too large to comfortably open or load with the import wizard. The task became an ingestion problem before it could become an analysis problem.

The work covered inspecting enough of the file to establish its structure, preparing a SQL destination, and using bcp from PowerShell to transfer the file to SQL Server. Troubleshooting included a placeholder server name, connection errors, bcp not being available on another machine, executable discovery, and confusion between an installed ODBC driver and the bcp command-line utility.

The project owner eventually reported a successful load and renamed the destination as a Raw table. We then returned to the unique-note extraction step for that new source. The raw-table schema and original import helper files are not present in this repository, so a complete production import is not claimed to be reproducible here. [Documented commands and script status](scripts.md).

This stage demonstrates an important practical distinction: the file and bcp client can reside on the workstation, while SQL Server executes the database work on the server. Being able to run a command in PowerShell does not mean every workstation has the same tools, permissions, or network access.

## 6. Separate Matching Cells from Unique Application Rows

The initial matching count answered a cell-occurrence question. The project owner expected a note to usually match one field per row and requested a separate unique-row count to verify that assumption.

That introduced two different overlap cases:

1. The same note can match two fields on one application row.
2. Two different notes can each match one field on the same application row.

Checking only the first case does not rule out the second. This explained why a description's total occurrence count could exceed its distinct matching-row count even when each note's multi-column excess was zero.

An early "extra matches" metric was the difference between cells and unique rows. It was easy to misread as the number of rows containing multiple notes. A single row with three matches contributes two extra occurrences, but only one multi-match row. The project owner judged that measure unhelpful for the intended audience, and the report was simplified.

The surviving design assigns a row ID before expanding fields, records matches at note-row-column grain, and derives distinct row sets for the required scope. It does not try to reconstruct overall unique coverage by adding overlapping detail counts. [Worked counting example](metrics.md).

## 7. Reconcile the Report with the Complete Source Population

The project owner compared an earlier Carburetor Float result with the actual source and found 43,778 source rows versus 43,684 rows with at least one listed-note match. The difference, 94, represented source rows outside that match set, not missing notes in the backlog.

This highlighted another distinction: **a note with no application match** and **an application with no listed-note match** are different exceptions. A note-level "No Match" row cannot describe every unmatched application. The overall report therefore needed an explicit all-application denominator, with matching subsets calculated within it.

That historical description example and the final approved aggregate snapshot are different observations. They should not be combined as if they came from the same versioned source run.

## 8. Connect the Mapping List to the Analysis

The mapping workbook supplied each unique note's status, with Mapped indicating mapped work and blank representing remaining work. It also contained mapping-related fields such as proposed Qdb text, parameters, and units. The impact report consumes the note and status; it does not validate the proposed mapping content.

A live Excel-to-SQL connection was discussed. The project owner preferred manual refresh because updates would be relatively infrequent. A CSV was imported into SQL and joined to the occurrence analysis.

This made two independent progress questions measurable: how many unique notes have mapped status, and how many application rows contain those notes. A mapped note with no application occurrence still counts toward backlog completion, while a frequent note may affect row coverage much more than another note.

The Python scripts apply the decisions supplied in their mapping workbooks; they do not generate the low-confidence export or update this SQL status list. The batch CSV records execution outcomes. PIM-state verification and manual status reconciliation are necessary before a note is marked Mapped. The SQL report then consumes the status list and application snapshot; it does not stand in for execution or verification.

## 9. Define Current Reach and the Full-List Opportunity

The overall report added all source rows, all unique notes, mapped-note count, completion percentage, mapped cells, current unique-row coverage, and current description reach. It also calculated potential rows and descriptions if every listed note were mapped.

Potential is calculated from the union of rows containing any listed note. It includes rows already covered by mapped notes. This gives the business a scope estimate without multiplying shared rows or mistaking the list's text occurrences for unique applications.

The reported stage was 35.80% mapped, with current note coverage on 132,834 unique application rows and full-list potential on 573,991 rows. These are occurrence metrics from the supplied report, not a count of deployed changes. [Complete results and business interpretation](business-case.md).

## 10. Turn the Analysis into a Team Workflow

The project owner and a catalog stakeholder selected description clusters using descending matching-cell counts across all listed notes. The first cluster included Carburetor Float, Carburetor Kit, Choke Thermostat, Choke Pull Off, and Pre Heater Hose.

A note may recur outside its current review cluster, so mapping work can have a wider description footprint than the cluster itself. The tracker made that reuse visible while retaining per-note detail.

The final communication format used a compact current-versus-potential table and an attached detailed report. The detailed report shows mapping status, matching descriptions and field names, counts of unique matching application rows, and the cell totals used to prioritize descriptions. It does not display the actual application records.

Updates every two weeks were planned in the draft email. This was a reporting intention, not a scheduled automation or a verified history of sent updates. The email also invited feedback on the format and metrics, reflecting the same emphasis on interpretability that shaped the query.

## What the End-to-End Story Demonstrates

The project connects Python mapping automation with practical data ingestion, review-backlog design, SQL analysis, performance troubleshooting, metric validation, and business communication. The tracker is a visible analytical output, not the entire solution. The larger contribution is joining execution with measurement: doing the mapping work and explaining its reach without confusing repeated matches with distinct applications.

The public reference model and automated tests were added later to make the report rules inspectable without company infrastructure. Source-derived automation tests additionally exercise execution controls and simulated browser flows. These portfolio additions are distinguished from the original scripts and do not substitute for live PIM or target SQL Server validation.

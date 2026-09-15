# Qdb Mapping Automation and Catalog Impact Analysis

**Python automation for catalog mapping, with SQL analysis that makes the work measurable.**

By [Can Kuvelet](https://github.com/Kuvelet)

Standard Motor Products | Python | Selenium | pandas | SQL Server | PowerShell

## Project Overview

A single catalog note can appear on thousands of application records. Mapping that note is one task, but its relevance can extend across many products and descriptions. Managing the work therefore requires more than a completed-item count: it requires a way to apply prepared mappings, identify priorities, and explain their application-level effect.

At Standard Motor Products, I developed three Excel-driven Python/Selenium scripts to automate Qdb mapping entry in the product information management (PIM) system. I paired that work with SQL Server analysis of **32,840 unique notes across 4,496,986 VIO application rows**.

The combined tracker brings together **Low Confidence, 100% Confidence, Date, and OE Number mappings**, including previously completed work. It connects the mapping list to the application catalog, shows where each note appears, and reports both current progress and the potential effect of completing the remaining list.

This repository is a **portfolio case study and code showcase**, not an installation package. The README explains the business reasoning and technical decisions; the original Python scripts and versioned SQL reporting logic provide the implementation detail.

## Results at a Glance

**25,556 of 32,840 unique notes are marked mapped: 77.82% completion.**

| Metric | Currently mapped | If all notes in the combined list were mapped |
|---|---:|---:|
| Unique notes mapped | 25,556 | 32,840 |
| Mapping completion | 77.82% | 100.00% |
| Unique VIO application rows affected | 269,523 | 680,521 |
| Share of all VIO application rows | 5.99% | 15.13% |
| Description groups affected | 473 | 749 |

The analysis searched **4,496,986 application rows**. Mapped notes occur in **405,197 matching cells**. There are **7,284 notes remaining** without mapped status.

Here, **affected** means that an application row contains at least one matching note in the relevant mapped or full-list scope. It is not a count of verified fitment corrections. The potential totals include the current effect.

These are project-owner-reported SQL results from the combined-list analysis, not results reproduced from the private application source in this repository.

## Contents

- [The business problem](#the-business-problem)
- [What Qdb is and why it matters](#what-qdb-is-and-why-it-matters)
- [Project scope](#project-scope)
- [The solution and my role](#the-solution-and-my-role)
- [The Python automation](#the-python-automation)
- [The SQL analysis](#the-sql-analysis)
- [Reading the reports](#reading-the-reports)
- [Making the counts trustworthy](#making-the-counts-trustworthy)
- [Prioritization and team reporting](#prioritization-and-team-reporting)
- [Business value and catalog health](#business-value-and-catalog-health)
- [Engineering decisions and lessons](#engineering-decisions-and-lessons)
- [The project files](#the-project-files)

## The Business Problem

A mapping spreadsheet describes work to perform, but it does not explain how that work relates to the catalog.

The same source text can appear repeatedly, in different fields, and under multiple product descriptions. Some notes occur frequently; others do not appear in the searched application data at all. Meanwhile, entering prepared mappings in the PIM system requires repeating the same filtering, selection, parameter-entry, and saving steps.

I needed to answer several connected questions:

- What are the distinct notes to review and map?
- How can I automate repeated entry while keeping the mapping decision with the reviewer?
- Which application fields and product descriptions contain each note?
- Which descriptions contain the most matching-note occurrences?
- How much work is complete, and how many distinct application rows contain those mapped notes?
- What is the total application-level effect represented by the complete mapping list?

Counting only notes would hide their frequency. Counting only occurrences would overstate the number of distinct application rows involved. Keeping separate spreadsheets for each mapping group would make the overall project harder to explain.

The solution connects **notes as work items, cells as occurrences, and application rows as the catalog records affected**.

## What Qdb Is and Why It Matters

**Qdb stands for Qualifier Database.** Maintained by the Auto Care Association, it standardizes fitment terminology used with ACES. Coded qualifiers represent application conditions consistently, and parameters hold variable values within those expressions. [Official Qdb overview](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb).

For example, an invented note such as "After serial 1000" contains both a condition and a value. A reviewer must determine what serial number is meant and whether the boundary is represented correctly. Selecting a qualifier without preserving that meaning would not be a successful mapping. This example is illustrative, not an official Qdb record.

### The ACES and PIES Connection

| Component | Purpose | Relationship to this project |
|---|---|---|
| ACES: Aftermarket Catalog Exchange Standard | Communicates product fitment information | Provides the application-data context for qualifier mapping |
| Qdb: Qualifier Database | Supplies standardized qualifier expressions supporting ACES | Provides the prepared qualifier selections and parameter structures entered through PIM |
| PIES: Product Information Exchange Standard | Communicates product information, including descriptions, attributes, and other product content | Complements fitment data in the broader catalog; not a mapping target of these scripts |

Sources: [Auto Care ACES](https://www.autocare.org/aces), [PIES](https://www.autocare.org/pies), and [Qdb](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb).

In the aftermarket, application conditions must remain understandable as information moves from a manufacturer to trading partners and part-lookup systems. Standardized qualifiers support more consistent interpretation and validation than unrestricted free text. [Qdb business context](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb).

That is the motivation for careful mapping, not a reason to automate judgment away. A standardized but incorrect condition is still a catalog problem. This project supports qualifier mapping; it does not generate ACES/PIES files, map PIES attributes, or certify standards compliance.

## Project Scope

The tracker consolidates four mapping groups:

| Mapping group | What it represents in the combined tracker |
|---|---|
| Low Confidence | Notes from the low-confidence Qdb report |
| 100% Confidence | Previously completed mappings from the 100% confidence group |
| Date | Previously completed date-related mappings |
| OE Number | Previously completed original-equipment-number mappings |

The imported group labels are `LowConfidence`, `100_Confidence`, `Date`, and `OEs`. These identify work categories, not predictions produced by the Python scripts. Mapping completion comes from the separate `MappingStatus` field.

**Brief background:** The tracker began with 11,656 low-confidence notes. I expanded it by adding my previously completed 100% Confidence, Date, and OE Number mappings so that one analysis could describe the broader Qdb mapping automation project. The current 77.82% completion rate refers to that combined population, not a directly comparable increase from the earlier low-confidence-only rate.

A unique note is a distinct cleaned text value across the entire imported list, not one item per group. If a note belongs to several groups, the report lists those groups together without multiplying its matches. Conflicting mapped statuses for the same note stop the query for correction.

## The Solution and My Role

The work has two connected parts: **Python applies prepared instructions through PIM; SQL measures the status and application context of the mapping list.** The handoff between them remains operator-managed.

```text
Source notes -> unique-note list -> mapping review and prepared Excel instructions
                                        |
                                        v
                            Python / Selenium PIM entry
                                        |
                                        v
                        Operator review and status maintenance
                                        |
                                        v
             Combined status-list import + VIO application view
                                        |
                                        v
                   SQL summary + note-by-description report
```

| Area | My contribution |
|---|---|
| Data preparation | Extracted distinct notes from raw SQL data and handled large-TSV ingestion using PowerShell and bcp |
| Automation | Developed three Python/Selenium workflows for no-, single-, and dual-parameter mapping entry |
| SQL development | Matched notes across 13 application fields and retained their note, row, column, and description relationships |
| Data quality | Accounted for duplicate notes, status conflicts, unmatched notes, and overlapping application matches |
| Performance | Used staged temporary tables and compact hash-assisted joins to make large-text analysis practical |
| Prioritization | Worked with Herman to select description clusters using matching-note occurrence totals |
| Reporting | Built a project summary and detailed tracker with business-readable measures |

The working mapping list is maintained outside SQL and imported manually when updated. This was appropriate for the expected refresh frequency. There is no automatic Excel-to-SQL synchronization, and the Python logs do not directly update the reporting table.

## The Python Automation

The three scripts process prepared Excel instructions and repeat actions in the PIM interface. They do not discover mappings, assign confidence, or decide whether two phrases mean the same thing.

| Script | Main workbook inputs | Mapping task |
|---|---|---|
| [automation_noparameter.py](automation_noparameter.py) | `Note`, `QDB Text` | Selects the supplied Qdb text without entering parameter values |
| [singleparameterauto.py](singleparameterauto.py) | `Note`, `QDB Text`, `Note Parameters` | Selects the qualifier and enters one supplied value |
| [dualparameter.py](dualparameter.py) | `Note`, `QDB Text`, `Note1 Parameter`, `Note2 Parameter` | Enters two supplied values for From/To-style mappings |

The no-parameter script can retain an optional `Note Parameters` value in its report, but does not enter it in PIM. The three script variants describe parameter-entry requirements; they are not a one-to-one assignment to the four mapping groups.

### The Repeated Workflow

After the operator logs in and navigates to the grid, each script:

1. Filters the Name column for the source note.
2. Locates the filtered result and removes its existing mapping.
3. Opens Add QDB and searches for the supplied qualifier text.
4. Selects the result and enters the required parameters, if any.
5. Clicks Save and waits for the interface.
6. Records the row outcome and proceeds through the workbook.

pandas handles workbook processing, Selenium WebDriver handles browser interaction, and CSV/text logs capture outcomes and runtime information. A configurable starting Excel row supports batch processing.

### Handling a Changing Interface

The difficult part was managing page state between actions. Grid refreshes, loading indicators, menus, and parameter widgets required explicit waits and fresh element lookups.

The scripts include quote-safe XPath construction, selected retries, loading checks, and dropdown handling. The single-parameter workflow also uses a JavaScript-dispatched context-menu event. These details support the repeated entry sequence in the particular PIM interface used for the project.

### Operator Responsibilities

The dual-parameter script selects parameter options by position, first index 0 and then index 1. It does not validate labels, range order, or units.

The original scripts record `Success` after the Save sequence without reading back the persisted mapping. They remove the previous mapping before adding its replacement, so the operation is not atomic. The original post-removal missing-result path records a skip and continues.

These behaviors are preserved in the original code. The scripts represent an **attended workflow for applying prepared decisions**, with operator review still needed to verify outcomes and maintain mapped status.

## The SQL Analysis

The latest report is [catalog_mapping_impact_v2.sql](catalog_mapping_impact_v2.sql). It reads the combined note/status/group list and the application view, and returns an overall summary plus note-by-description detail.

### Prepare a Distinct Work List

The basic analytical unit starts with distinct source text:

```sql
SELECT DISTINCT [Note]
FROM [dbo].[LowConfidence_Raw];
```

Separating a raw import from a unique-note list preserves the original records while creating a manageable review population. For an export too large to inspect or load comfortably through the import wizard, I used PowerShell and bcp to bring the TSV into SQL Server before extracting notes.

The current combined analysis trims ordinary leading and trailing spaces, validates statuses, and counts each distinct cleaned note once. Blank notes, an empty list, unexpected status values, and conflicting statuses are rejected before the large application view is read.

The imported group header may be `Group` or have surrounding spaces. The query resolves that header from SQL metadata and quotes its identifier with `QUOTENAME`. Multiple distinct groups for one note are aggregated into a semicolon-separated list.

### Search the Application Fields

The analysis searches these 13 fields:

**BodyStyle, BrakeType, CarbNumber, CarbType, Color, Connection Type, Cylinder Head Type, Emissions, FootNote, Lead Length, Note, OE Number, Split Year.**

Position is excluded. Group membership, prepared Qdb text, parameter values, UOM, and the imported `MatchingColumns` field do not restrict the occurrence search.

A match is **whole-cell equality after ordinary-space trimming**, with case and accents significant under the explicit binary collation used for note matching. It is not a substring, fuzzy, or semantic match. In particular, the SQL does not parse dates or split OE-number lists into separate values.

### Preserve the Counting Unit

Each row returned by the application view receives a temporary ID **before** its 13 searched fields are expanded through `CROSS APPLY (VALUES ...)`.

The retained match structure is:

```text
Note ID + Application Row ID + Matching Column
```

This allows the report to count individual matching cells, collapse them to one note/application pair, and then deduplicate application IDs across multiple mapped notes. Description context is carried through those relationships.

### Make Long-Text Matching Practical

The note text remains `nvarchar(max)`. A fixed-width SHA2-256 hash provides a compact comparison key, followed by full-text equality:

```sql
ON n.NoteHash = CONVERT(binary(32), HASHBYTES('SHA2_256', c.CleanValue))
AND n.NoteText = c.CleanValue
```

The hash assists matching; it does not replace text verification. Indexed temporary tables retain reusable intermediate results instead of repeatedly rebuilding the same matches.

The query stages input validation, notes, the application snapshot, matching cells, distinct note/row pairs, and report aggregates. `COUNT_BIG` supports large counts, and `STRING_AGG` receives `nvarchar(max)` values for long lists.

Only temporary analysis tables are written. The source list and application view are read-only, and the temporary tables are released after the two reports are returned.

## Reading the Reports

### 1. Overall Project Summary

The one-row summary answers two questions: **how much of the combined mapping list is complete, and how many application records contain its notes?**

| Measure | Interpretation |
|---|---|
| Total VIO rows searched | All rows returned by the application view; denominator for application percentages |
| Total unique notes | Distinct cleaned notes across the combined list, including notes with no application match |
| Notes marked mapped | Notes whose imported mapping status is `Mapped` |
| Mapping completion percent | Mapped notes divided by total unique notes |
| Cells containing mapped notes | Individual searched field values matching mapped notes |
| Unique VIO rows containing mapped notes | Application rows containing at least one mapped-note match, counted once overall |
| Percent of all VIO rows affected | Those distinct mapped-note rows divided by all rows searched |
| Descriptions containing mapped notes | Distinct description groups with at least one mapped-note match |
| Full-list potential rows, percentage, and descriptions | The same application-level scope considering all listed notes, whether mapped or not |

**77.82% measures completion of note-level work; 5.99% measures the application-row effect of the mapped subset.** They have different denominators and are not expected to be similar.

### 2. Note-by-Description Detail

A normal detail row represents one note within one description. It shows:

| Detail field | What a reader learns |
|---|---|
| Report Row Type | Whether this is a matched note/description, an unmatched note, or a description with no listed-note match |
| VIO Description | The description associated with the matching application rows |
| This Description - Matching Cells If All Combined QDB Mapping List Notes Were Mapped | Total occurrences of all listed notes within that description; used for prioritization |
| Searched Note | The cleaned source note being analyzed |
| Note Group | Its mapping category, or a semicolon-separated list if it belongs to multiple groups |
| Mapping Status | `Mapped` or `Not Mapped`, based on the imported status |
| VIO Match Status | Whether the note was found anywhere in the searched application fields |
| This Note In This Description - Matching Cells | Individual matching field values for this note in this description |
| This Note In This Description - Unique Matching VIO Rows | Distinct application rows containing this note within this description |
| This Note In This Description - Matching VIO Columns | Distinct field names where it matched, listed with semicolons |
| This Note Across All Descriptions - Number Of Descriptions | Number of description groups in which this note occurs |

The report contains **counts of matching application rows, not the application records themselves**.

A note found nowhere appears as `Note With No VIO Match`, with zero note-level cells and rows. A description with no listed-note match receives its own description-only row; note-specific fields are null because no note is associated with it. This prevents exceptions from disappearing from the report.

The description-level cell total repeats beside each note in that description. It is a ranking value, not an additive detail measure. Similarly, a note's description count repeats wherever that note appears.

## Making the Counts Trustworthy

### Cells and Rows Answer Different Questions

Consider this invented example, with both Note A and Note B marked mapped:

| Application row | Description | Note field | CarbType field |
|---|---|---|---|
| 101 | Description A | Note A | Note B |
| 102 | Description A | Note A | No listed note |
| 103 | Description B | Note A | No listed note |

Note A matches three cells on three rows. Note B matches one cell on one row. Together, they match **four cells on three unique application rows** because row 101 contains both notes.

Neither note needs to match multiple columns on the same row for this overlap to occur. Different notes can share an application row.

That explains how the actual mapped-note results can contain **405,197 cells but 269,523 unique rows**. The difference is not the number of rows with multiple matches: one shared row can contribute more than one additional match.

### Safe Ways to Read the Totals

- For a single note within one description, cells equal rows only if that note matches at most one searched field on each row.
- Summing per-note unique-row counts can double-count shared application rows. Use the overall summary for the distinct project-wide total.
- Filtering the detail report to `Mapped` and summing its **note-level matching cells** reconciles to the overall mapped-cell count for the same run.
- Do not sum the repeated description-priority totals or repeated per-note description counts.

### What an Application Row Represents

These counts refer to output records from the VIO application view, not the numeric `VIO` field, a sum of vehicles in operation, or distinct real-world vehicles. Each source-view output row receives a separate ID; duplicate-looking rows remain separate.

Descriptions are grouped using the database's collation, without additional description trimming in v2. Null descriptions are counted as one separate group and displayed as `(No description)`.

An unmatched note and an unmatched application row are different cases. A note may never appear in the application source; an application may simply contain none of the listed notes. The overall denominator still includes every application row searched.

## Prioritization and Team Reporting

Herman and I established a description-by-description work order using **matching-note occurrences in descending order across all unique notes in the Low Confidence Qdb report**.

The first description cluster included **Carburetor Float, Carburetor Kit, Choke Thermostat, Choke Pull Off, and Pre Heater Hose**. We continued the mapping work according to those agreed priorities.

The ranking used matching **cells**, which identify concentrations of recurring note text. It was not a revenue, severity, or unique-row ranking. The combined report now exposes that same occurrence metric across all four groups, supporting review of priorities within the expanded scope without implying that a new order has already been agreed.

A note selected while reviewing one description may also appear under others. The detail report makes that broader context visible, while the overall summary avoids counting shared application rows more than once.

For team communication, I prepared a concise progress table with the detailed report attached and planned updates every two weeks. Colleagues can see completion, current and potential application effect, and the basis for description prioritization without interpreting SQL.

## Business Value and Catalog Health

### Focus Review Where the Notes Recur

The distinct-note list organizes the work into decisions rather than repeated source records. Description-level occurrence totals identify concentrations of that work, and the group field distinguishes mapping categories in the same report.

This makes prioritization explainable: the team can point to the catalog context and frequency behind a selected description instead of relying on spreadsheet order.

### Separate Expertise from Repeated Entry

The Python workflows put repetitive PIM interactions into code. Prepared mapping selection and parameter review remain human responsibilities, while the scripts repeat the entry sequence and record outcomes.

The demonstrated contribution is an automated entry workflow, not a measured percentage reduction in labor or errors. No controlled time-savings benchmark was retained.

### Put Project Completion in Catalog Context

The combined tracker accounts for both ongoing low-confidence work and earlier completed mapping groups. It reports **25,556 mapped notes** alongside **269,523 distinct affected application rows**, making the difference between completed tasks and catalog effect visible.

Completing the remaining list represents a potential total of **680,521 unique application rows across 749 description groups**. That includes the current effect, equivalent to **410,998 additional application rows** in the full-list set beyond the currently mapped subset. It does not mean every future note contributes new rows.

### Support Consistent Application Information

The intended business value is a more consistent representation of application conditions, with less interpretation required when those conditions are consumed downstream. Correct mapping can support clearer part selection and more manageable catalog data.

Those benefits depend on accurate decisions, successful persistence, deployment, and downstream use. The tracker measures status and source-text occurrence, not delivered fitment corrections, sales increases, or return reductions.

**Catalog health is broader than mapping completion.** Vehicle configurations, qualifier meaning, parameters, product attributes, and downstream presentation need their own checks. This project contributes a practical mapping and measurement workflow within that broader responsibility.

## Engineering Decisions and Lessons

### Preserve the Relationship Before Counting It

The essential modeling decision was to keep note, application-row, and matching-column identities until each metric could be calculated at the correct level. Deduplicating too early would lose occurrences; aggregating too late without row identity would overstate application totals.

### Stage Expensive Work and Keep Full Text

An early query ran for more than an hour. Temporary-table staging and indexed hash-assisted matching made later iterations substantially quicker in the project run experience, although no controlled speedup figure was recorded.

Earlier long-text index warnings and `STRING_AGG` size errors informed the use of compact hash keys and `nvarchar(max)` text. The result was a query organized around reusable intermediate relationships, with full-value matching retained.

### Treat Missing Matches as Useful Information

Unmatched notes stay in the completion denominator and detail report. They can still represent mapping work even when the searched application source does not contain their text. Description-only exceptions likewise show where the imported list has no match.

### Make Categories Informative, Not Multipliers

Combining lists required a single note identity across groups, consistent status handling, and group aggregation that does not duplicate report rows. Group labels explain origin; they do not change equality rules or turn one note into several work items.

### Distinguish Execution, Status, and Verification

A successful browser sequence, a manually maintained mapped status, and a verified persisted mapping are different forms of evidence. Keeping those responsibilities explicit makes both the automation and its reported results easier to assess.

Together, the work demonstrates **Python automation, SQL analysis, large-file handling, data modeling, performance troubleshooting, automotive catalog knowledge, and stakeholder communication**.

## The Project Files

The latest analysis is **v2**. The earlier SQL file remains unchanged so the previous version stays available.

| File | Purpose |
|---|---|
| [automation_noparameter.py](automation_noparameter.py) | Original no-parameter mapping workflow |
| [singleparameterauto.py](singleparameterauto.py) | Original single-parameter mapping workflow |
| [dualparameter.py](dualparameter.py) | Original dual-parameter mapping workflow |
| [catalog_mapping_impact_v2.sql](catalog_mapping_impact_v2.sql) | Current combined-list report, including note groups and note-level matching-cell counts |
| [catalog_mapping_impact.sql](catalog_mapping_impact.sql) | Earlier reporting edition, retained as the v1 reference under its original filename |

The Python files preserve the supplied scripts, with the private PIM URL replaced by a placeholder and a short archival header added. Workbook names, batch offsets, logging labels, and execution behavior are retained. They execute work at module level and should not be imported or run merely to inspect them.

The v2 SQL follows the latest operational combined-list query, with source identifiers and environment-specific header text sanitized for publication. It retains the operational description grouping under `DATABASE_DEFAULT`; the earlier portfolio edition normalized descriptions differently. The two files therefore should not be treated as interchangeable executions of the same report.

The SQL requires SQL Server 2017+ and database compatibility level 110+. Private inputs and environment identifiers are intentionally absent, so this is reporting code for inspection, not a ready-to-run deployment package. No live private SQL Server or PIM execution is part of this repository update.

There is intentionally no demo dataset, test package, CI workflow, deployment tooling, or installation guide. The repository showcases the actual scripts and explains the work in one place.

### Attribution and Scope

The company name and aggregate figures were approved by the project owner for this case study. Raw company records, mapping workbooks, credentials, private endpoints, and licensed reference-database content are excluded.

This is an independent portfolio case study, not an official Standard Motor Products or Auto Care Association publication. Referenced standards and names belong to their respective owners. No software redistribution license is granted here.

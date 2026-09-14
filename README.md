# Qdb Mapping Automation and Catalog Impact Analysis

**A Python and SQL project connecting catalog-mapping work to its application-level reach.**

By [Can Kuvelet](https://github.com/Kuvelet)

Standard Motor Products | Python | Selenium | pandas | SQL Server | PowerShell

## Project Overview

One catalog note can appear on thousands of application records. That makes a mapping decision a small unit of work with potentially broad relevance. It also makes progress surprisingly difficult to explain: completing one note is not the same as improving one application, and counting every occurrence is not the same as counting distinct applications.

At Standard Motor Products, I worked on the Low Confidence Qdb mapping project to address two connected needs: **apply prepared mappings through the product information management system, and understand where that work matters across the catalog.**

I used three Python/Selenium scripts to automate repetitive PIM entry for mappings with no parameters, one parameter, or two parameters. I used SQL Server to connect the unique-note backlog and mapping status to the application catalog, identify review priorities, and build a progress tracker.

The analysis covered **11,656 unique notes and 4,486,697 application rows**. At the reported stage, **4,173 notes were marked mapped, representing 35.80% of the backlog**. The complete note list occurred on **573,991 unique application rows across 631 description groups**.

This repository is a **case study and code showcase of that work**, not a reusable software product or a reproduction kit. The explanation is here in the README; the four project scripts are linked below.

## Contents

- [The business problem](#the-business-problem)
- [What Qdb is and why it matters](#what-qdb-is-and-why-it-matters)
- [My role and approach](#my-role-and-approach)
- [How the project developed](#how-the-project-developed)
- [The Python automation](#the-python-automation)
- [The SQL analysis](#the-sql-analysis)
- [Making the counts trustworthy](#making-the-counts-trustworthy)
- [Prioritization and team reporting](#prioritization-and-team-reporting)
- [Reported progress and potential reach](#reported-progress-and-potential-reach)
- [Business value and catalog health](#business-value-and-catalog-health)
- [What I learned](#what-i-learned)
- [The project files](#the-project-files)

## The Business Problem

The low-confidence report provided notes requiring mapping review, but a list alone could not answer the questions needed to manage the project:

- Which notes were distinct review items, rather than repetitions of the same text?
- Where did each note appear in the application catalog?
- Which product descriptions contained the greatest concentration of those occurrences?
- How could prepared mappings be entered without manually repeating the same interface sequence?
- How much of the backlog was mapped, and how broadly did those notes appear?
- What would the full list's application coverage look like when all its notes were mapped?

These questions crossed several kinds of work. There was a data-preparation problem, a repeated-entry problem, a prioritization problem, and a measurement problem.

Reviewing only the raw records would obscure the distinct decisions. Reviewing only unique notes would obscure their application context. Reporting only a mapped-note count would obscure their reach.

The project connected those views: **a note as a review item, its occurrences as context, and application rows as the basis for catalog coverage.**

## What Qdb Is and Why It Matters

**Qdb stands for Qualifier Database.** Maintained by the Auto Care Association, it supplies standardized, coded fitment expressions used with ACES. Some qualifiers contain parameters that hold variable values. [Official Qdb overview](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb).

In plain language, a fitment qualifier expresses a condition attached to an application. An invented example such as "After serial 1000" illustrates why the wording alone may not be enough: a reviewer must establish which serial number is meant and how the boundary should be represented. The appropriate qualifier and its parameter must preserve that meaning. This is a teaching example, not an official Qdb entry or recommended mapping.

### Where ACES and PIES Fit

| Component | What it communicates | Connection to this project |
|---|---|---|
| ACES: Aftermarket Catalog Exchange Standard | Product fitment information, including the applications for which a part is cataloged | The mapping initiative concerns application qualifications |
| Qdb: Qualifier Database | Standardized qualifier expressions supporting ACES | The Python scripts enter supplied Qdb selections and parameter values |
| PIES: Product Information Exchange Standard | Product information such as descriptions, attributes, and other product content | Complementary catalog context; this project does not perform PIES attribute mapping or validate PIES files |

Sources: [Auto Care ACES](https://www.autocare.org/aces), [PIES](https://www.autocare.org/pies), and [Qdb](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb).

For an aftermarket business, catalog information must remain useful beyond the manufacturer's own system. Important application conditions need to survive interpretation by data recipients and part-lookup users. Auto Care identifies more consistent interpretation and validation among the benefits of coded qualifiers. [Qdb business context](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb).

That is the reason to invest in careful mapping, not a reason to automate judgment away. **A standardized but incorrect condition is still a catalog problem.** Low confidence identifies work for review; it does not automatically mean that a part's fitment is wrong.

## My Role and Approach

I connected the execution work to the analysis needed to organize and explain it.

| Area | My contribution |
|---|---|
| Data preparation | Extracted unique notes from raw SQL data; later worked through large-TSV ingestion using PowerShell and bcp |
| Mapping automation | Used Excel-driven Python/Selenium scripts for no-, single-, and dual-parameter PIM mapping workflows |
| SQL development | Matched notes across application fields, added description context, and staged the analysis to address execution and text-size problems |
| Metric design | Separated matching cells, per-note matching rows, and overall unique application coverage |
| Prioritization | Worked with Herman to select description clusters using matching-note occurrence totals |
| Communication | Created an overall progress table and a detailed report with business-readable column names |

The responsibilities remained distinct: a person supplied the mapping decision, Python repeated the PIM entry, and SQL measured status and occurrence. The mapping-status list was refreshed manually; the scripts did not automatically update the SQL tracker.

## How the Project Developed

### Start with a Manageable Review Population

The SQL work began with a straightforward distinct-note query against an existing raw table:

```sql
SELECT DISTINCT [Note]
FROM [dbo].[LowConfidence_Raw];
```

This separated repeated records from the unique text values that needed review. Keeping the raw table separate preserved the source context while providing a smaller, reusable backlog.

A unique text value was a useful unit of work, but not proof that the same mapping would be valid in every context. I therefore needed to find where each note was used.

### Add Field and Product Context

The application view was in another database on the same SQL Server. I expanded the search beyond the `Note` column because listed text could also appear in fields such as `CarbType`, `FootNote`, and `BodyStyle`.

The requirement evolved from a total match count to counts by matching column, then to matching descriptions. Early versions combined distinct descriptions with semicolons. As description-based prioritization became the focus, the report changed to one detail row per note and description.

Notes with no matches stayed visible. Otherwise, unresolved items would disappear simply because the occurrence query did not find them.

### Make the Analysis Practical

An early query ran for more than an hour. The expanding joins and text aggregations made repeated analysis difficult.

I worked through a staged approach using temporary tables, indexed hash-assisted joins, and reusable match results. This also addressed long-text index warnings and `STRING_AGG` size errors. Later execution was substantially quicker according to the project run experience, although no controlled speedup benchmark was retained.

At one point, description aggregation was limited to Position matches to reduce the work. It was expanded again after optimization. Position was subsequently removed from the final search scope, while Lead Length was added.

### Bring in a Large Export

Later, another TSV was too large to inspect comfortably or import through the wizard. I used PowerShell and bcp to load it into SQL Server, working through connection and command-availability issues along the way.

After the load succeeded, the destination remained a Raw table, and the unique-note list was extracted separately. This extended the same workflow to data that was impractical to work with interactively.

The ingestion commands were supporting work, not an additional application. The repository therefore keeps the four main scripts rather than introducing an import framework.

### Connect Mapping Status and Simplify the Report

The working mapping list identified each unique note as `Mapped` or blank. Importing that list into SQL made it possible to compare backlog progress with application reach.

A live Excel-to-SQL connection was considered, but I chose manual refresh because updates were expected to be relatively infrequent.

The report evolved through several exploratory metrics before settling into two complementary outputs: an overall summary and note-by-description detail. The final design kept the measures that supported decisions and removed confusing derived counts.

These stages describe how the reasoning developed. They do not imply a precise calendar sequence between all Python and SQL work.

## The Python Automation

The three scripts automate repeated actions in the PIM interface using prepared Excel instructions. They do not discover mappings or score confidence.

| Script | Workbook inputs | Mapping work |
|---|---|---|
| [automation_noparameter.py](automation_noparameter.py) | `Note`, `QDB Text` | Selects the supplied Qdb text without adding parameter values |
| [singleparameterauto.py](singleparameterauto.py) | `Note`, `QDB Text`, `Note Parameters` | Selects the qualifier and enters one value |
| [dualparameter.py](dualparameter.py) | `Note`, `QDB Text`, `Note1 Parameter`, `Note2 Parameter` | Enters two supplied values for From/To-style work |

The no-parameter script can also retain an optional `Note Parameters` value in its report, but does not enter it in PIM.

### The Repeated Workflow

After the operator logs in and navigates to the grid, each script processes workbook rows and:

1. Filters the Name column for the source note.
2. Locates the filtered result.
3. Removes its existing mapping.
4. Opens Add QDB and searches the supplied qualifier text.
5. Selects the result and enters any required parameters.
6. Clicks Save, waits for the interface, and records the outcome.

The scripts use pandas for workbook processing, Selenium WebDriver for browser interaction, and CSV/text logs for row outcomes and runtime information. The operator can set the starting Excel row for a batch.

The practical challenge was not simply clicking buttons. The page changed while the script was working. The code includes explicit waits, loading-indicator checks, fresh element lookups after grid refresh, quote-safe XPath construction, and selected retries around dynamic menus and dropdowns. The single-parameter script also uses a JavaScript-dispatched context-menu event.

The dual-parameter script selects visible parameter options by position, first index 0 and then index 1. It does not validate semantic labels, range order, or units. Prepared input and operator review remain important.

### What the Automation Achieved

The scripts moved a repeated sequence of PIM actions into code, allowing the operator to process prepared mapping instructions with per-row reporting. That is the automation contribution: **repeat the entry work after the mapping decision has been made.**

The original scripts label completed Save actions `Success`, but do not read back the persisted mapping. They also remove the old mapping before adding the new one; replacement is not atomic, and the original post-removal missing-result path logs a skip and continues. These behaviors are preserved in the showcase rather than silently rewritten.

The files document an attended, environment-specific workflow. They are not presented as unattended production software or a general-purpose mapping engine.

## The SQL Analysis

The single [catalog_mapping_impact.sql](catalog_mapping_impact.sql) file shows the reporting logic. Its two inputs are the unique-note/status list and the application view.

### Search Scope

The final analysis searches 13 fields:

**BodyStyle, BrakeType, CarbNumber, CarbType, Color, Connection Type, Cylinder Head Type, Emissions, FootNote, Lead Length, Note, OE Number, Split Year.**

Position is excluded. A match means whole-cell text equality after the documented cleaning rules, not a substring or a semantically similar phrase.

### Preserve Context Before Aggregating

The SQL assigns a row ID to each application-source row before expanding the searched fields with `CROSS APPLY (VALUES ...)`.

The intermediate matching structure retains:

```text
Note ID + Application Row ID + Matching Column
```

That structure is the basis for both occurrence counts and distinct-row coverage. The report can preserve the relationship to the source description without treating each expanded cell as a separate application.

### Use Compact Keys for Long Text

Long notes caused index-key size warnings in earlier queries. SHA2-256 hashes provide a fixed-width join key, while the full text remains part of the match condition:

```sql
ON n.NoteHash = CONVERT(binary(32), HASHBYTES('SHA2_256', c.CleanValue))
AND n.NoteText = c.CleanValue
```

The hash assists matching; it does not replace verification. The displayed SQL uses `nvarchar(max)` for text and aggregation, ordinary-space trimming, and explicit binary collation. Case and accent differences therefore remain significant.

### Stage the Work Once

Temporary tables separate note preparation, the application snapshot, matched cells, distinct note/row pairs, and reporting aggregates. They make intermediate results reusable instead of repeatedly rebuilding the same relationships.

These are analysis tables in the SQL session, not permanent catalog tables. The script returns reports and does not deploy Qdb mappings.

### Two Outputs, Two Audiences

| Output | What it shows | How it is used |
|---|---|---|
| Overall summary | Total notes, mapped notes, completion percentage, mapped-note cells, current unique-row coverage, and full-list row/description potential | Communicates scope and progress at project level |
| Note-by-description detail | Mapping status, matching descriptions and columns, unique matching-row counts, number of descriptions per note, and all-list cell totals per description | Supports review, investigation, and description prioritization |

The detail report shows **counts of matching application rows**, not the actual application records. It retains unmatched notes and descriptions with no listed-note matches.

## Making the Counts Trustworthy

The most important analytical lesson was that a match can be counted at different levels. Those levels answer different business questions.

| Measure | What it counts |
|---|---|
| Unique notes | Distinct review items in the low-confidence report |
| Matching cells | Individual searched field values that match listed notes |
| This note's matching rows | Distinct application rows containing a particular note |
| Overall matching rows | Distinct application rows containing at least one note in the selected mapped or full-list scope |
| Description reach | Distinct description groups containing those notes |

### Why Per-Note Counts Do Not Always Add Up

Consider this invented illustration:

| Application row | Description | Note field | CarbType field |
|---|---|---|---|
| 101 | Description A | Note A | Note B |
| 102 | Description A | Note A | No listed note |
| 103 | Description B | Note A | No listed note |

Note A matches three rows. Note B matches one. Together they produce **four matching cells on three unique application rows**, because row 101 is shared.

Neither note matches more than one column on any row. The overlap comes from different notes appearing on the same application. This explains why a per-note "extra column matches" value of zero does not eliminate overall overlap.

The SQL calculates overall coverage from the union of row IDs. It does not add per-note row counts and call the result unique.

### Reconcile the Denominator

In an earlier check, Carburetor Float had **43,778 source rows**, of which **43,684 contained a listed-note match**. The remaining **94** were outside that matched subset.

A note with no application match is not the same as an application with no listed-note match. That distinction led to clearer denominators and reporting language. This historical example is separate from the aggregate snapshot below.

An application source row is also not the numeric VIO value. The report does not sum vehicles in operation or count distinct real-world vehicles. Each source-view output row is counted as a record; duplicate-looking source rows remain separate.

## Prioritization and Team Reporting

Herman and I prioritized the mapping work **description by description**, using **matching-note occurrences in descending order across all unique notes in the Low Confidence Qdb report**.

The first description cluster included:

- Carburetor Float
- Carburetor Kit
- Choke Thermostat
- Choke Pull Off
- Pre Heater Hose

This provided a recognizable product context and a measurable reason for the work order. The ranking used matching **cells**, not unique application rows. It highlighted concentrations of recurring note text; it was not a revenue, severity, or incremental-coverage ranking.

A note can recur beyond the description currently being reviewed. Its mapping may therefore be relevant to additional descriptions, subject to confirming that the meaning is appropriate in those contexts.

For communication, I developed a compact progress table and an attached detailed report. The planned update cadence was every two weeks. The aim was to let colleagues see what was completed, why the next cluster was chosen, and what the full project scope represented without needing to interpret the SQL.

## Reported Progress and Potential Reach

The application population searched contained **4,486,697 rows**.

| Metric | Reported mapped-note stage | If all listed notes were mapped |
|---|---:|---:|
| Unique notes marked mapped | 4,173 | 11,656 |
| Share of note backlog mapped | 35.80% | 100.00% |
| Matching cells containing those notes | 132,834 | Full-list total not reported |
| Unique application rows containing those notes | 132,834 | 573,991 |
| Share of application rows searched | 2.96% | 12.79% |
| Description groups containing those notes | 11 | 631 |

At that stage, **7,483 notes remained without mapped status**. The difference between current and full-list coverage was **441,157 additional potential application rows**.

The most useful interpretation is that **35.80% of the note backlog was marked mapped, while the entire backlog occurred on 12.79% of the application rows searched**. These percentages measure different things. Notes vary in frequency and can share rows.

The full-list scenario includes the currently covered rows. It is not an additional 573,991 applications, a forecast of delivered changes, or a count of corrected fitments. Likewise, a row containing a mapped note can still contain other unresolved content.

These figures are the project-owner-reported SQL results. They establish the reported status and occurrence scope; no measured labor savings, sales increase, or return reduction is claimed.

## Business Value and Catalog Health

The business value comes from connecting work that would otherwise be difficult to manage as a whole.

### Make Specialist Effort More Focused

A unique-note backlog turns repeated text into a review population. Description-level occurrence analysis adds the context and concentration needed to choose a work order. The team can explain why it is starting with a particular product group rather than simply working through spreadsheet order.

### Automate Repetitive Entry

Once a mapping is prepared, the PIM steps are repetitive. The Python scripts perform those actions and record row outcomes, while leaving mapping selection and verification with the operator. This separates specialist judgment from the interface work needed to apply it.

### Make Progress Meaningful

A mapped-note total measures task status. It does not explain catalog coverage. The SQL tracker adds that second view, showing where the mapped notes occur and how much broader the complete backlog is.

This makes stakeholder reporting more useful: the discussion can distinguish work completed, repeated text in scope, and distinct applications involved.

### Support More Consistent Catalog Content

The project supports a path toward more consistently represented application conditions: identify the note, review its meaning, apply the appropriate mapping, and understand where the source text appears.

For an aftermarket company, the intended downstream value is clearer application information, less interpretation work, and better-supported part selection. Those benefits depend on correct mapping decisions, deployment, and downstream handling. They are the business rationale, not measured outcomes of this report.

**Catalog health is broader than mapping completion.** Vehicle configurations, product information, qualifier correctness, parameters, and downstream presentation still need their own checks. Qdb work complements the broader ACES/PIES catalog process; it does not certify compliance or prove that the entire catalog is correct.

The immediate demonstrated contribution is a practical way to carry out the mapping work, select priorities, and communicate its scope with understandable measures.

## What I Learned

The hardest part was not writing a match condition. It was agreeing on what the result meant.

Separating notes, cells, and rows changed the report from a collection of large totals into a usable decision tool. Preserving unmatched notes and reconciling against the complete source population made the analysis more honest. Reworking slow queries made iteration practical. Revising the column names made the result understandable to people who had not written the SQL.

The automation work reinforced a different lesson: repeated browser actions still need attention to state, timing, parameter order, and failure handling. Applying a prepared decision and verifying its result are separate responsibilities.

Together, the project demonstrates **Python automation, SQL analysis, large-file handling, data modeling, performance troubleshooting, domain understanding, and stakeholder communication**. Its central contribution is connecting execution with measurement, without confusing repeated matches with distinct applications or potential reach with completed improvements.

## The Project Files

| File | Purpose |
|---|---|
| [automation_noparameter.py](automation_noparameter.py) | Original no-parameter mapping workflow |
| [singleparameterauto.py](singleparameterauto.py) | Original single-parameter mapping workflow |
| [dualparameter.py](dualparameter.py) | Original dual-parameter mapping workflow |
| [catalog_mapping_impact.sql](catalog_mapping_impact.sql) | Consolidated overall and detailed impact-report logic |

The Python files preserve the supplied scripts, with the private PIM URL replaced by a placeholder and a short archival header added. Original workbook names, batch offsets, logging labels, and execution behavior are retained. They run work at module level, so they should not be executed or imported merely to inspect them.

The SQL file is a consolidated presentation of the reporting logic developed through the project discussion, not a byte-for-byte archive of the last production query. Source identifiers are placeholders. Explicit input validation, long-text handling, and deterministic collation retained from repository preparation are presentation-edition changes. The underlying private source data and full historical query revisions are not included.

This repository intentionally has no demo dataset, test package, CI workflow, deployment tooling, or installation guide. Its purpose is to explain the work and make the relevant code easy to inspect.

### Attribution and Scope

The company name and aggregate figures were approved by the project owner for this case study. Raw company records, actual mapping workbooks, credentials, and licensed reference-database content are excluded.

This is an independent portfolio case study, not an official Standard Motor Products or Auto Care Association publication. Referenced standards and names belong to their respective owners. No software redistribution license is granted here.

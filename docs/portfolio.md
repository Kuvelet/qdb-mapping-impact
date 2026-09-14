# Resume, Portfolio, and Interview Copy

The company name and aggregate figures below were approved by the project owner for this case-study draft. Confirm organizational publication and code-sharing requirements before publishing. Preserve the distinctions between reported progress, potential reach, and deployed improvements.

## Project Title

**Qdb Mapping Automation and Catalog Impact | Python + SQL**

## One-Sentence Positioning

Built attended Python/Selenium workflows to apply spreadsheet-supplied Qdb mappings in PIM, with SQL Server analysis to prioritize note review, track progress, and measure application-level catalog reach.

## Resume Bullets: Balanced Version

- Developed Excel-driven Python/Selenium workflows for no-, single-, and dual-parameter Qdb mappings at Standard Motor Products, paired with SQL analysis linking 11,656 low-confidence notes to 4.49 million application rows.
- Designed cross-column exact matching and distinct-row aggregation across 13 application fields, separating repeated note occurrences from unique application coverage to prevent inflated impact reporting.
- Tracked 35.80% note-mapping completion and identified full-backlog potential coverage of 573,991 application rows across 631 description groups, supporting stakeholder-led review priorities and progress reporting.

Use two or three bullets according to available space. The third bullet reports a project stage, not a final outcome or a claim of sole responsibility for all mappings.

## Resume Bullets: Data-Engineering Emphasis

- Automated PIM filtering, Qdb selection, parameter entry, and Save actions with Python, pandas, and Selenium, with per-row CSV outcomes and attended exception handling.
- Built a staged T-SQL pipeline using temporary tables, SHA2-256 hash-assisted exact joins, `CROSS APPLY`, and explicit note-row aggregation to analyze catalog-note occurrence at application scale.
- Used PowerShell and bcp to move a large TSV export into SQL Server, retaining raw records separately from the unique-note review population.
- Added input validation, duplicate-status conflict detection, unmatched-record retention, and documented metric grains to improve the reliability and interpretability of mapping-impact reports.

## Resume Bullets: Business-Analysis Emphasis

- Converted a catalog mapping backlog into a description-level prioritization framework, distinguishing task completion, note occurrence, and application reach for stakeholders.
- Established a repeatable reporting format connecting mapping status to current and potential catalog coverage, with clear denominators and safeguards against double-counting.

## Short Portfolio Card

**Problem:** Repeated low-confidence catalog notes and a large export needed to become a usable review backlog, with enough application context to decide which mapping work to prioritize.

**Solution:** Python/Selenium applies the mapping decisions supplied in Excel, using separate workflows for zero, one, and two parameters. After reviewed status updates, SQL connects mapping progress and the review population to application data. Supporting ingestion and preparation make the data usable, while the tracker ranks descriptions and measures current and potential coverage without double-counting shared rows.

**Reported scale:** 11,656 unique notes; 4.49 million application rows; 573,991 rows of full-list potential. The public repository includes synthetic data and executable tests, not company records.

**Tools and concepts:** Python, Selenium WebDriver, pandas, and openpyxl for mapping automation; SQL Server and T-SQL for analysis; PowerShell and bcp for ingestion; relational modeling, validation, set-based aggregation, and ACES/Qdb domain knowledge. The separate `qdb_impact/` Python package and GitHub Actions support the portfolio demo and tests, not the original mapping execution.

## Portfolio Case Study: Ready-to-Adapt Narrative

### Context

At Standard Motor Products, I worked on a Python automation and SQL analysis project supporting Qdb mapping and aftermarket catalog standardization. Python scripts performed the mapping work. SQL provided a way to analyze low-confidence notes, track mapping status, and understand the reach of that work across the application catalog.

### My Approach

I used pandas to read prepared mapping instructions from Excel and Selenium to repeat the PIM actions for zero-, one-, and two-parameter mappings. The scripts handle grid filtering, Qdb text selection, parameter entry, and Save, with explicit waits, selected UI retries, per-row reporting, and attended exception handling. Mapping selection and persisted-state review remain separate responsibilities.

I developed SQL analysis around the mapping status and review population. The SQL analysis began with distinct-note extraction from an existing raw table and investigation of where those notes occurred in application data. When a later TSV export was impractical to open or import interactively, I used PowerShell and bcp to load it into SQL Server and kept the raw source separate from the unique-note list.

I developed the analysis iteratively: adding per-column counts and description context, retaining unmatched notes, and restructuring the SQL after long-running queries and text/index-size issues. I then connected note-level mapping status to the application analysis. The final report searches 13 fields and summarizes matching cells, individual note/application pairs, and unique application rows across the mapped list.

That separation matters because one application can contain several listed notes, and the same note can appear in several fields. Simply adding individual match counts would overstate the number of distinct applications reached. I made those counting rules explicit and retained notes with no matches so exceptions remained part of the workflow.

I also worked with a catalog stakeholder to prioritize review by description, using the number of matching note occurrences across the full list. This provides an understandable product context for mapping work while recognizing that a note may be reused across multiple descriptions.

### Reported Results

The analysis covered 4,486,697 application rows and 11,656 unique notes. At the reported stage, 4,173 notes were marked mapped, representing 35.80% completion. Those notes appeared on 132,834 unique application rows. The complete backlog had potential reach across 573,991 unique application rows and 631 description groups.

These results describe occurrence coverage, not confirmed production corrections or measured financial gains. The tracker provides the evidence needed to prioritize and monitor the work; correct mapping decisions, deployment, and downstream validation remain separate responsibilities.

### Technical Takeaway

The most important lesson was to define the grain of every metric and test it against the business question. The reporting definitions evolved as we reconciled results with source counts and examined overlap. Staging intermediate results, assigning application-row IDs before field expansion, and using hash-assisted exact joins made the workflow easier to explain and maintain. The public edition adds a synthetic reference model and regression tests so another analyst can inspect those rules without access to private data.

### Original Python Mapping Scripts

The supplied scripts are spreadsheet-driven PIM automations, not fuzzy-matching or machine-learning engines. They remove existing mappings before adding supplied replacements and log outcomes after Save without independently reading back the final mapping. The portfolio edition preserves the workflows while adding local preview, explicit execution/replacement acknowledgement, bounded batches, clearer status semantics, and offline tests. Those hardening changes are portfolio additions, not claimed as original production features.

## Interview Answer: About 60 Seconds

"I built a Python automation and SQL analysis workflow for Qdb mapping. Python and Selenium handled repetitive PIM entry using reviewed Excel instructions, and I used SQL Server to understand the results, prioritize low-confidence notes, and measure where those notes appeared in the application catalog.

I linked mapping statuses to exact matches across thirteen fields and separated matching cells from distinct application rows. That prevented double-counting when multiple notes shared a row. I used the occurrence totals to support description-level prioritization and produced an overall summary with detailed exceptions.

At the reported stage, the backlog was 35.80% mapped. The full list appeared on about 574 thousand unique application rows. I describe that as potential coverage, not completed corrections. The project demonstrates how I combine Python automation, SQL implementation, data-quality reasoning, and business communication."

## Questions to Be Ready For

| Question | Strong, accurate answer |
|---|---|
| What exactly was automated? | Repetitive PIM entry: locate a note, replace its mapping with Excel-supplied Qdb text, enter zero/one/two values, save, and log. Mapping selection, login, and persisted-state review remain human responsibilities. |
| Why hashes? | Narrow join keys for long Unicode text, with a full-text equality predicate retained. |
| Why not sum per-note rows? | Different notes can match the same row, so overall coverage is a union of row IDs. |
| What is the PIES connection? | Complementary catalog governance; this implementation targets qualifier occurrence and does not validate PIES. |
| Did it reduce returns? | That was not measured. I would link deployed mapping changes to defined downstream metrics before making that claim. |
| What would you build next? | Versioned mapping decisions and report snapshots, target-engine validation, and incremental-priority metrics based on remaining work. |

## Skills Demonstrated

Python/Selenium browser automation; pandas workbook processing; dynamic UI waits and exception handling; large-file ingestion; PowerShell and bcp troubleshooting; raw-versus-curated data separation; SQL aggregation and query design; data-model grain; deduplication and overlap analysis; exception handling; deterministic occurrence matching; large-text handling; testable metric contracts; requirements clarification; stakeholder reporting; catalog-data governance; and precise communication of business impact.

Python mapping automation is part of the confirmed project. Do not extend that claim to automated mapping discovery, unattended production scheduling, automatic ACES/PIES generation, quantified savings, or a performance multiplier without supporting evidence.

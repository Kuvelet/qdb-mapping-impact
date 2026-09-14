# Business Case: Automating Catalog Mapping and Measuring Its Reach

## Executive Summary

The business problem was not simply finding repeated text. It was making low-confidence catalog data usable, organizing it into a manageable review backlog, deciding where to spend catalog-review effort, and explaining the reach of that work across an aftermarket application catalog.

At Standard Motor Products, Python scripts were used for mapping automation, with SQL used to analyze the project and its catalog impact. A Low Confidence Qdb report provided the note population for review and analysis. Application data supplied the operating context: which descriptions contained those notes, which fields they appeared in, and how often they recurred.

The two layers answer different business needs. **Python executes the mapping workflow; SQL explains its status and reach.** Automation without analysis would not, by itself, explain which descriptions to prioritize or how broadly mapped notes appear. Analysis without the mapping execution would describe the work without performing it. The supplied scripts show how this works: Excel contains the chosen mapping text and values, and Selenium repeats the corresponding PIM actions. Review and verification remain human responsibilities.

The reported population contained **11,656 unique notes** and **4,486,697 application rows**. At the reported stage, **4,173 notes were marked mapped**, equivalent to **35.80% backlog completion**. Those notes occurred on **132,834 unique application rows**. The entire list occurred on **573,991 unique rows across 631 description groups**.

The project combines script-based mapping automation with a defensible work queue and progress report, supported by raw-data ingestion, unique-note extraction, and iterative SQL analysis. The reported coverage is not proof that every matching application row has been corrected in production, nor a measured financial-return study. The [project story](project-story.md) explains both roles; the [script guide](scripts.md) identifies the original components and their source availability.

## Value Starts Before the Final Report

| Work stage | Practical business contribution | Boundary of the claim |
|---|---|---|
| Large-file ingestion | Makes a difficult-to-open export available to database analysis | No measured import-time or labor-savings claim |
| Unique-note extraction | Organizes repeated text into a note-level review backlog while retaining raw context | One text value is not automatically one universally valid mapping |
| Python mapping automation | Applies Excel-supplied Qdb selections through PIM with zero, one, or two parameters and per-row logs | Does not choose or semantically approve mappings; Save is not independently verified, and no time-savings benchmark was supplied |
| Application-context analysis | Reveals where a note recurs across fields and descriptions | Exact occurrence does not prove semantic equivalence |
| Metric validation | Keeps shared application rows from inflating the reported reach | Does not independently validate source fitment correctness |
| Prioritization and communication | Gives reviewers a product-focused queue and stakeholders understandable progress | Ranking by cells is not a revenue or risk ranking |

Together, these stages create a Python automation and SQL analysis workflow. The tracker is its reporting layer. Expected operational value includes more repeatable execution and better-directed review, but no quantified labor savings or error reduction is claimed without measurement.

The automation addresses the repeated keyboard-and-mouse work after a decision has been prepared: filtering the PIM grid, finding the qualifier, entering its values, and saving. Separating no-, single-, and dual-parameter work accommodates different input shapes. Per-row logs help reconcile what was attempted and what stopped. This makes specialist judgment reusable without implying that the script can replace it. [How the Python workflows operate](python-automation.md).

## Why This Matters in the Automotive Aftermarket

**Qdb is the Qualifier Database**, used with ACES for standardized fitment expressions. This project addresses the work of mapping source notes to supplied Qdb selections and measuring where those notes appear. Readers new to the industry can start with the [plain-language explanation and examples](standards-context.md).

An aftermarket catalog has to help someone select a part in a specific application context. Vehicle identification, application constraints, product attributes, and the wording presented to trading partners all contribute to that decision. A product record may be rich and complete yet still be difficult to use if an important application qualification is inconsistent or ambiguous.

ACES is the fitment-data exchange standard; PIES is the product-information exchange standard. Their roles are complementary. [Auto Care ACES overview](https://www.autocare.org/aces), [PIES overview](https://www.autocare.org/pies).

Within the fitment workflow, a free-text qualifier may have abbreviations, wording variants, exceptions, or context that requires specialist judgment. The team needs to preserve meaning while deciding whether and how a standard qualifier can represent it. A low-confidence designation is a **review signal**, not proof that the source fitment is wrong.

The operational challenge is scale and reuse. The same note can appear under several descriptions, while one application row can contain several listed notes. Reviewing a note once may have broad reuse, but careless counting can make that reuse look like more distinct applications than actually exist.

## The Decision the Tracker Enables

The tracker makes the following management questions visible:

| Management question | Evidence used | Decision supported |
|---|---|---|
| Where is the largest concentration of listed note text? | All-note matching-cell totals per description | Choose a description cluster for specialist review |
| Is the mapping backlog being completed? | Unique notes marked mapped / unique notes listed | Track task progress and unresolved work |
| How broadly does completed work appear in the catalog? | Distinct application rows containing mapped notes | Describe current mapping coverage without duplicate counting |
| How large is the full-list opportunity? | Distinct rows containing any listed note | Set scope and communicate potential reach |
| What needs investigation rather than automatic action? | Unmatched notes and descriptions | Review source scope, text differences, or stale backlog entries |

This separates **work completed**, **text occurrences**, and **catalog reach**. None is a substitute for the others.

## Prioritizing Work Description by Description

The project owner and a catalog stakeholder prioritized descriptions by **matching note occurrences in descending order**, considering all unique notes in the Low Confidence Qdb report. The initial cluster included Carburetor Float, Carburetor Kit, Choke Thermostat, Choke Pull Off, and Pre Heater Hose. Individual cluster counts were not provided and are not invented here.

This approach has two operational advantages. It groups review into a recognizable product context, and it directs attention toward descriptions with many occurrences of the backlog's notes. A common note can also appear outside the selected cluster, so its eventual mapping may be relevant to other descriptions.

The priority metric is intentionally occurrence-based. It is **not** a sales ranking, a safety-severity ranking, or a measure of newly covered unique rows. A description with many matches on a relatively small number of already-covered rows can rank highly. That is appropriate when the goal is standardizing repeated text; it is not guaranteed to maximize incremental application coverage per hour.

If the operational goal changes, extend prioritization with remaining unmapped-cell counts, new-row coverage after excluding already-covered rows, review effort, and business-risk input. Those are future measures, not features claimed as implemented in the current tracker.

## What the Reported Results Establish

| Evidence | Interpretation | What it does not establish |
|---|---|---|
| 4,173 of 11,656 notes marked mapped | 35.80% of the note backlog has mapped status | 35.80% of applications, revenue, or catalog quality is improved |
| 132,834 mapped-note cells and 132,834 unique rows | At this reported stage, every covered row contributes exactly one mapped-note cell | Overlap cannot occur among the full list or in future updates |
| 573,991 potential unique rows | 12.79% of searched rows contain at least one note from the complete list | 573,991 new rows beyond current coverage |
| 631 potential description groups | The full list has broad cross-description reach | 631 part numbers, brands, or validated product classifications |
| 441,157 remaining potential rows | Full-list row set minus current mapped-note row set | A committed deployment plan or a measured defect count |

The remaining note backlog is **7,483**. A note-count completion percentage and an application-coverage percentage naturally move at different rates because notes have different frequencies and may share rows. These figures should be presented together, not forced into a single "catalog health" score.

## How It Can Improve Catalog Health

The following is a **business mechanism and measurement plan**, not a set of observed downstream outcomes.

| Catalog-health dimension | How this project contributes | Evidence needed to show improvement |
|---|---|---|
| Consistency | Finds recurring note usage and supports one reviewed mapping decision for repeated text | Before/after audit of approved qualifier usage |
| Interpretability | Gives reviewers the product descriptions and source fields surrounding a note | Specialist sign-off that mapped wording preserves constraints |
| Traceability | Connects each reviewed note to its matching descriptions, fields, and row counts | Versioned mapping decisions and published run metadata |
| Review completeness | Retains unmatched notes instead of silently dropping them | Exception closure rate and reason codes |
| Distribution readiness | Identifies a population to check after mappings are approved and deployed | Export validation and trading-partner acceptance results |
| Operational control | Provides a shared backlog denominator and repeatable progress metrics | Regular snapshots and a documented refresh process |

The immediate value is better visibility and decision quality: reviewers can explain why a description was selected, managers can distinguish progress from potential, and report consumers can understand the denominator behind each percentage.

Potential downstream benefits include less interpretation work, fewer catalog-related clarification cycles, more consistent partner-facing content, and better-supported part selection. Those benefits depend on correct mappings, deployment, partner behavior, and other catalog processes. Auto Care identifies standardization benefits such as easier qualifier interpretation and validation; this project has not independently measured those effects. [Auto Care Qdb overview](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb).

## A Mapping Is Not a Production Correction

A complete business process has several distinct milestones:

1. Identify a note and understand its application context.
2. Review the appropriate reference content and approve a meaning-preserving mapping.
3. Record the mapping decision, including necessary parameters and units.
4. Apply the approved change through a controlled catalog process.
5. Validate affected fitments, generated files, and downstream presentation.
6. Confirm partner acceptance and monitor operational outcomes.

This tracker reads the mapping-status flag and measures note occurrence. It does not prove that steps 2 through 6 were correctly completed. The same text may have different meanings in different contexts, so cross-description reuse must still be reviewed.

## A Credible Follow-Up Measurement Plan

To establish benefits beyond coverage, compare a defined baseline with a post-deployment period for the same scope. Record mapping versions, source versions, export versions, and the actual deployment date. Distinguish a note being approved from it being implemented and distributed.

Useful follow-up measures include rejected application records per submitted record, catalog-related clarification cases per order or lookup, sampled qualifier accuracy, and review time per accepted note. If measuring returns, use fitment-related returns per fulfilled line and account for changes in sales mix, product availability, seasonality, and return-reason quality. A before/after difference alone is not enough to attribute causality to mapping.

An optional business-case formula is:

```text
Estimated net benefit =
    validated review/maintenance labor savings
  + attributable reduction in catalog-related rework costs
  - mapping review, implementation, and operating costs
```

No dollar values are populated because the necessary time, cost, transaction, and outcome data were not provided. Application rows are not sales transactions, vehicles in operation, or distinct customers.

## Business Value in One Paragraph

This project combines Python-based mapping automation with SQL-based impact analysis for an aftermarket catalog-improvement program. Python performs the mapping work, while SQL connects the note population and mapping status to product descriptions, repeated occurrences, and unique application coverage. That combination supports both execution and prioritization. The reported metrics establish status and potential reach; improvements in customer experience, returns, and revenue remain downstream hypotheses to validate after approved mappings are deployed.

# Evidence, Claims, and Limitations

## Evidence Register

| Item | Evidence available | How it may be described |
|---|---|---|
| Project scale and progress | Project-owner-supplied aggregate SQL output | Reported results, not independently reproduced measurements |
| Company attribution | Project owner confirmed public use of company name and totals | A project at Standard Motor Products, not an endorsed company product |
| Working SQL design | Existing project query reviewed and adapted | SQL Server implementation with explicit aggregation grains |
| Large-file ingestion and unique-note preparation | Command history, SQL snippets, and user-reported successful bcp load | Part of the original workflow; public command examples are reconstructed, not recovered helper files |
| Original Python mapping automation | All three supplied files inspected without executing them | Attended Selenium workflows applying Excel-supplied mappings through PIM; adaptations and limits documented |
| Adapted Python execution controls | Offline import/CLI tests and simulated browser flows | Guard and control-flow verification, not live PIM compatibility or persisted mapping validation |
| Performance improvement | User reported an early run lasting over an hour and a later query being much faster | Qualitative improvement; no numerical speedup claim |
| Prioritization workflow | Project conversation identifies a jointly chosen description cluster and cell-based ranking | Stakeholder-informed prioritization using occurrence counts |
| Synthetic correctness | Locally executed reference tests and final-SELECT relational checks | Tested demo arithmetic and report joins, with engine limitations stated |
| SQL Server execution of this public edition | Optional checker supplied, not run during portfolio build | Not yet verified on a target SQL Server |
| Revenue, returns, labor savings, or partner rejection rates | No before/after outcome data supplied | Proposed benefits and future measures only |

The [approved aggregate file](../evidence/approved_project_metrics.json) is the single source for the company chart and checks. The underlying raw catalog and mapping records are deliberately absent. The original data snapshot date, SQL Server configuration, and target standards/reference versions were not supplied.

## Verified Arithmetic from the Supplied Aggregates

```text
4,173 / 11,656 x 100 = 35.80% note completion, rounded
132,834 / 4,486,697 x 100 = 2.96% current row coverage, rounded
573,991 / 4,486,697 x 100 = 12.79% full-list potential coverage, rounded
573,991 - 132,834 = 441,157 additional potential rows
11,656 - 4,173 = 7,483 notes not marked mapped
```

Checking these ratios verifies arithmetic, not the upstream correctness of the company source data or the mapping decisions. The equality between current mapped cells and current unique rows applies only to the reported mapped subset; it does not establish that all-note matches lack overlap.

## Important Limitations

- Matching is strict, full-cell text occurrence, not semantic equivalence. Related wording may be missed.
- Mapping status is trusted input. The SQL report does not validate qualifier IDs, parameters, units, approval history, or standards versions.
- Python applies supplied values; it does not decide whether a mapping is semantically correct. Dropdown order and broad UI locators require review.
- PIM replacement removes the old mapping before adding the new one. There is no rollback or persisted-state readback. A submitted Save is not independent confirmation of a completed mapping.
- Python CSV execution outcomes do not automatically populate SQL MappingStatus. The handoff is manually reviewed and refreshed.
- A note with the same wording in different contexts may require different treatment; context review remains necessary.
- A covered row can still contain unmapped notes or other catalog defects. The overall metric is not a complete health score.
- Every source-view output row is counted. Duplicate source rows and join multiplication are retained, not diagnosed automatically.
- Counts are not weighted by the numeric VIO field, revenue, order volume, or product criticality.
- Only 13 specified fields are searched. Position and all other fields are out of scope.
- Full-list potential assumes every listed note could be mapped; it is a scope scenario, not an approved delivery forecast.
- Current coverage is included in potential coverage. Repeated description metrics and per-note rows are not freely additive.
- Missing descriptions are retained as a separate group. Description text is not a canonical product identifier.
- Source materialization does not itself enforce a transactionally consistent cross-source snapshot.

## What Was Tested

The Python suite covers hand-calculated counts, note and column overlap, input conflicts, empty applications, no-match notes, missing descriptions, duplicate source records, long notes, strict text behavior, status changes, and randomized set-cardinality invariants. The SQL-report suite extracts the actual two final SELECTs and compares their SQLite-executed relational results against the reference across several scenarios.

SQLite substitutions do not validate SQL Server compilation, SHA2-256 implementation, Unicode collation details, temporary-table optimizer behavior, memory consumption, isolation, index usage, or `STRING_AGG` engine behavior. The optional SQL Server smoke checker covers a full synthetic run but is not a performance test or an exhaustive integration suite.

Automation tests additionally check dependency-free import/help, preview behavior, execution acknowledgement, HTTP controls, headers, row bounds, formatting, and simulated zero/one/two-parameter flows. They check that an initial missing result skips, disappearance after removal stops, and browser cleanup is attempted on interruption. Selenium is replaced with test doubles; no real browser, PIM endpoint, mapping workbook, or licensed content is used. The actual Excel engine/dependency combination and current PIM UI still require authorized integration testing.

The GitHub Actions workflow is supplied for future pushes. A workflow file existing locally does not mean it has already passed on GitHub.

## Safe Portfolio Language

**Use:** "Built a tracker that identified 573,991 application rows containing notes in the full mapping backlog."

**Avoid:** "Corrected 573,991 applications." Mapping approval and deployment were not measured by the query.

**Use:** "Tracked 35.80% completion of the unique-note backlog."

**Avoid:** "Improved catalog quality by 35.80%." That is not the denominator or the measured outcome.

**Use:** "Combined Python mapping automation with SQL analysis of low-confidence notes and application coverage."

**Avoid:** "Guaranteed ACES/PIES compliance through fully autonomous mapping." The inspected scripts execute supplied decisions in an attended session; they do not infer or semantically approve mappings, validate standards compliance, or verify persisted state. The synthetic reference model is a separate reporting aid.

**Use:** "Staged and indexed matching analysis; later runs were reported as faster."

**Avoid:** "Delivered a 100x speedup." No controlled benchmark supports that figure.

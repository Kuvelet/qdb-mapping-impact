# Metric Dictionary and Reconciliation

## Read This First

**A matching cell is one occurrence of a listed note in one searched field of one application row.** A unique application row counts once within the stated grouping, even if several cells or notes match it.

Here, "VIO rows" means rows returned by the application source. It does not mean the sum of a numeric vehicles-in-operation field. "Description" is a source text group, not a guaranteed part number or PCdb classification. A row containing a mapped-status note is within that mapping's occurrence footprint; it is not necessarily a corrected or fully standardized row.

## Overall Summary: One Row per Run

| Exact output header | Meaning and calculation |
|---|---|
| Total VIO Rows Searched | All source application rows, including rows without a note match |
| Total Unique Notes Present In Low Confidence QDB Report | Distinct cleaned note text after duplicate validation; includes unmatched notes |
| Notes Marked Mapped | Unique notes whose normalized status is Mapped, even with no application match |
| Project Completion Percent | Notes Marked Mapped / Total Unique Notes x 100 |
| Cells Containing Mapped Notes | Count of note-row-column matches for mapped-status notes |
| Unique VIO Rows Containing Mapped Notes | Distinct source-row IDs containing at least one mapped-status note |
| Percent Of All VIO Rows Affected | Current mapped-note unique rows / all searched rows x 100; occurrence coverage, not confirmed changes |
| Descriptions Containing Mapped Notes | Distinct description groups on current covered rows; a missing-description group counts once if present |
| Unique VIO Rows Affected If All Unique Notes Present In Low Confidence QDB Report Were Mapped | Distinct source-row IDs matching any listed note, mapped or not; includes currently covered rows |
| Percent Of All VIO Rows Affected If All Unique Notes Present In Low Confidence QDB Report Were Mapped | Full-list potential unique rows / all searched rows x 100 |
| Unique Descriptions Affected If All Unique Notes Present In Low Confidence QDB Report Were Mapped | Distinct description groups matching any listed note, including a matching NULL group |

Percentages are rounded to two decimals. With zero application rows, row-coverage percentages are NULL because the denominator is zero. With applications but no matches, coverage is zero. An empty note list is rejected rather than reported as a completed project.

The long "Affected" headers preserve the established report interface. In presentations, use the more precise labels **current mapped-note coverage** and **full-list potential coverage**. The query does not update rows.

## Detail: Note by Description, with Exceptions

| Exact output header | Meaning |
|---|---|
| Report Row Type | Indicates a note found in a description, a note with no match anywhere, or a description with no listed-note match |
| VIO Description | Description group associated with the row; NULL may mean a missing source description or an unmatched note, so also read row type |
| This Description - Matching Cells If All Low Confidence QDB Report Notes Were Mapped | All listed-note cell occurrences in this description, regardless of current mapping status; repeated on each note row in the description |
| Searched Note | One cleaned note from the mapping list; NULL on a description-only exception |
| Mapping Status | Mapped or Not Mapped; NULL when no searched note is associated with the row |
| VIO Match Status | Whether the note occurs anywhere in the searched fields, independently of mapping status |
| This Note In This Description - Unique Matching VIO Rows | Count of distinct application rows in this description containing this particular note |
| This Note In This Description - Matching VIO Columns | Distinct searched field names containing the note in that description, separated by semicolon and space |
| This Note Across All Descriptions - Number Of Descriptions | Number of description groups in which this note occurs; repeated across that note's detail rows |

The detail contains **counts of application rows**, not the actual application records, part numbers, or vehicle configurations. The field-name list is aggregated across the note's matches in the description; it does not imply every field matched on every row.

An unmatched note has zero matching rows and descriptions, and NULL description-level potential. A real description with no listed-note match has zero description-level potential and NULL note-specific fields.

## A Small Example You Can Count by Hand

Synthetic notes A and B are mapped; C is not mapped. D is mapped but absent from the application data. E is unmapped and absent.

| Application row | Description | Listed-note cells |
|---|---|---|
| 1 | Fuel Valve | A in BodyStyle; A in Note; B in Connection Type; C in FootNote |
| 2 | Fuel Valve | A in Note |
| 3 | Fuel Sensor | C in Note |
| 4 | Fuel Valve | None |
| 5 | NULL | B in Note |
| 6 | Service Hose | None in searched fields; an A in Position is excluded |

The fixture uses readable invented phrases in place of A through E. See [synthetic inputs](../examples/synthetic_catalog.json).

**Current progress:** 3 of 5 notes are marked mapped, so completion is 60%. D contributes to progress but not coverage.

**Mapped matching cells:** row 1 contributes 3, row 2 contributes 1, and row 5 contributes 1, totaling 5 cells.

**Unique rows with mapped notes:** rows 1, 2, and 5, totaling 3 rows. Counting row 1 separately for A and B would inflate the overall count.

**Full-list potential:** rows 1, 2, 3, and 5, totaling 4 rows. Potential includes the 3 already covered rows. Only row 3 is additional.

**Fuel Valve priority:** 5 cells from all listed notes: 4 in row 1 and 1 in row 2. This value repeats for A, B, and C in the detail. It is not 5 unique rows and must not be added three times.

## Why Sums May Not Agree

Per-note unique-row counts overlap. A's two Fuel Valve rows plus B's one Fuel Valve row equals three note-row pairs, but only two distinct Fuel Valve application rows. Summing those counts answers a different question than counting overall unique rows.

Likewise, mapped cells can exceed mapped unique rows because the same note can match several fields on one row. Even if each individual note matches at most one field per row, several different notes may still share that row.

Description-level priority totals use **all notes**, while current mapped-cell totals use **only mapped notes**. Those two values need not agree. To reconcile all-note cells by description, take one description total per group, not every repeated detail value.

## Invariants Worth Testing

```text
mapped-note unique rows <= full-list potential unique rows <= all source rows
mapped-note unique rows <= mapped-note matching cells
current mapped-note descriptions <= full-list potential descriptions
all notes mapped => current unique rows equal full-list potential unique rows
changing status alone does not change full-list potential
one all-note cell total per description sums to all-note matching cells
```

These are set-based relationships, not assumptions that every note has the same frequency. The tests exercise overlaps, missing descriptions, excluded fields, no matches, and empty application populations.

## Scope of a 100% Completion Claim

The denominator is the unique notes in the input report, not every qualifier in the catalog. Full completion does not measure qualifier correctness, reference-version validity, deployment, or partner acceptance. Adding newly discovered notes changes the denominator and may reduce the completion percentage even while completed-note count rises.

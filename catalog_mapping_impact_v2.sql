/*
Qdb mapping project: combined-list impact analysis, portfolio version 2.
The earlier reporting edition is preserved as catalog_mapping_impact.sql.
See README.md for the project scope, results, and counting definitions.

Private source identifiers are placeholders; this is code for inspection, not
a ready-to-run deployment package. The reporting body follows the operational
combined-list query, including group labels and note-level matching-cell counts.

Input contracts:
  [YOUR_MAPPING_DATABASE].[dbo].[YOUR_MAPPING_STATUS_TABLE]:
      Note, MappingStatus, Group (the group header may have surrounding spaces)
  [YOUR_APPLICATION_DATABASE].[dbo].[YOUR_APPLICATION_VIEW]:
      Description and the 13 searched application fields

Only temporary analysis tables are written. All stages use one SQL session.
Results: 1. Overall mapped-note effect and full-list potential.
         2. Note-by-description detail with group, cells, rows, and columns.
Unmatched notes and descriptions with no listed-note match remain visible.
Potential totals include the current effect. Repeated description totals in
the detail report must not be summed, nor may per-note unique rows be added
to obtain an overall distinct-row total.

The match uses full values after ordinary-space trimming, with case and accents
significant. Group, MatchingColumns, Qdb text, parameters, and UOM do not filter
the occurrence search. Position is excluded. Duplicate cleaned notes count once;
conflicting mapped statuses stop the run. Multiple groups are listed together.

Each application-view output row receives its own ID before column expansion.
These are application-row counts, not SUM(VIO). Duplicate-looking rows remain
separate. Descriptions retain DATABASE_DEFAULT collation with no extra trimming;
NULL descriptions count as one group. No-match notes show zero note-level cells
and rows; description-only records show NULL in note-specific fields.

SQL Server 2017+; database compatibility level 110+.
*/
USE [YOUR_MAPPING_DATABASE];
SET NOCOUNT ON;

DROP TABLE IF EXISTS #QdbImpactInput;
DROP TABLE IF EXISTS #QdbImpactDistinctNotes;
DROP TABLE IF EXISTS #QdbImpactNotes;
DROP TABLE IF EXISTS #QdbImpactNoteGroups;
DROP TABLE IF EXISTS #QdbImpactVio;
DROP TABLE IF EXISTS #QdbImpactCells;
DROP TABLE IF EXISTS #QdbImpactNoteRows;
DROP TABLE IF EXISTS #QdbImpactCoveredRows;
DROP TABLE IF EXISTS #QdbImpactNoteStats;
DROP TABLE IF EXISTS #QdbImpactDescriptions;
DROP TABLE IF EXISTS #QdbImpactDescriptionPotential;
DROP TABLE IF EXISTS #QdbImpactNoteDescriptions;
DROP TABLE IF EXISTS #QdbImpactNoteDescriptionColumns;

-- Validate the imported list before reading the large VIO view.
-- Resolve the actual group header without renaming the imported table's columns.
DECLARE @GroupColumn sysname;
DECLARE @GroupColumnCount int;
SELECT @GroupColumn = MIN([name]), @GroupColumnCount = COUNT(*)
FROM sys.columns
WHERE object_id = OBJECT_ID(N'dbo.YOUR_MAPPING_STATUS_TABLE', N'U')
  AND LTRIM(RTRIM([name])) = N'Group';

IF @GroupColumnCount <> 1
    THROW 50005, 'Expected exactly one Group column, optionally with surrounding spaces, in YOUR_MAPPING_STATUS_TABLE.', 1;

CREATE TABLE #QdbImpactInput (
    NoteText nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
    StatusText nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL,
    GroupName nvarchar(max) COLLATE Latin1_General_100_BIN2 NULL
);

DECLARE @ReadNotesSql nvarchar(max) = N'
INSERT INTO #QdbImpactInput (NoteText, StatusText, GroupName)
SELECT
    LTRIM(RTRIM(CONVERT(nvarchar(max), [Note]))),
    UPPER(LTRIM(RTRIM(COALESCE(CONVERT(nvarchar(max), [MappingStatus]), N'''')))),
    NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(max), ' + QUOTENAME(@GroupColumn) + N'))), N'''')
FROM [YOUR_MAPPING_DATABASE].[dbo].[YOUR_MAPPING_STATUS_TABLE];';
EXEC sys.sp_executesql @ReadNotesSql;

IF NOT EXISTS (SELECT 1 FROM #QdbImpactInput)
    THROW 50001, 'The imported mapping table is empty. Check the import first.', 1;

IF EXISTS (SELECT 1 FROM #QdbImpactInput WHERE NoteText IS NULL OR NoteText = N'')
    THROW 50002, 'The imported table contains a blank Note. Correct it before running this report.', 1;

IF EXISTS (SELECT 1 FROM #QdbImpactInput WHERE StatusText NOT IN (N'', N'MAPPED'))
    THROW 50003, 'MappingStatus must contain Mapped or be blank/NULL. Check the imported values.', 1;

-- Identical duplicate entries count once. Conflicting statuses require correction.
SELECT DISTINCT
    NoteText,
    CONVERT(bit, CASE WHEN StatusText = N'MAPPED' THEN 1 ELSE 0 END) AS IsMapped
INTO #QdbImpactDistinctNotes
FROM #QdbImpactInput;

IF EXISTS (
    SELECT NoteText
    FROM #QdbImpactDistinctNotes
    GROUP BY NoteText
    HAVING COUNT_BIG(*) > 1
)
    THROW 50004, 'The same cleaned Note has both mapped and blank statuses. Resolve the conflict first.', 1;

SELECT
    IDENTITY(int, 1, 1) AS NoteId,
    NoteText,
    IsMapped,
    CONVERT(binary(32), HASHBYTES('SHA2_256', NoteText)) AS NoteHash
INTO #QdbImpactNotes
FROM #QdbImpactDistinctNotes;

CREATE UNIQUE CLUSTERED INDEX IX_QdbImpactNotes_Id ON #QdbImpactNotes (NoteId);
CREATE INDEX IX_QdbImpactNotes_Hash ON #QdbImpactNotes (NoteHash);

-- One group list per note preserves the report's existing row counts.
SELECT
    n.NoteId,
    STRING_AGG(CONVERT(nvarchar(max), g.GroupName), N'; ')
        WITHIN GROUP (ORDER BY g.GroupName) AS NoteGroups
INTO #QdbImpactNoteGroups
FROM #QdbImpactNotes AS n
INNER JOIN (
    SELECT DISTINCT NoteText, GroupName
    FROM #QdbImpactInput
    WHERE GroupName IS NOT NULL
) AS g ON g.NoteText = n.NoteText
GROUP BY n.NoteId;

CREATE UNIQUE CLUSTERED INDEX IX_QdbImpactNoteGroups_NoteId
ON #QdbImpactNoteGroups (NoteId);

-- Read the VIO view once; assign row IDs before expanding the searched columns.
SELECT
    IDENTITY(bigint, 1, 1) AS VioRowId,
    CONVERT(nvarchar(max), a.[Description]) COLLATE DATABASE_DEFAULT AS [Description],
    a.[BodyStyle], a.[BrakeType], a.[CarbNumber], a.[CarbType], a.[Color],
    a.[Connection Type], a.[Cylinder Head Type], a.[Emissions], a.[FootNote],
    a.[Lead Length], a.[Note], a.[OE Number], a.[Split Year]
INTO #QdbImpactVio
FROM [YOUR_APPLICATION_DATABASE].[dbo].[YOUR_APPLICATION_VIEW] AS a;

CREATE UNIQUE CLUSTERED INDEX IX_QdbImpactVio_Id ON #QdbImpactVio (VioRowId);

-- Store only matching cells. Hash indexes avoid indexing long note text.
SELECT n.NoteId, a.VioRowId, s.MatchColumn
INTO #QdbImpactCells
FROM #QdbImpactVio AS a
CROSS APPLY (VALUES
    ('BodyStyle',          CONVERT(nvarchar(max), a.[BodyStyle])),
    ('BrakeType',          CONVERT(nvarchar(max), a.[BrakeType])),
    ('CarbNumber',         CONVERT(nvarchar(max), a.[CarbNumber])),
    ('CarbType',           CONVERT(nvarchar(max), a.[CarbType])),
    ('Color',              CONVERT(nvarchar(max), a.[Color])),
    ('Connection Type',    CONVERT(nvarchar(max), a.[Connection Type])),
    ('Cylinder Head Type', CONVERT(nvarchar(max), a.[Cylinder Head Type])),
    ('Emissions',          CONVERT(nvarchar(max), a.[Emissions])),
    ('FootNote',           CONVERT(nvarchar(max), a.[FootNote])),
    ('Lead Length',        CONVERT(nvarchar(max), a.[Lead Length])),
    ('Note',               CONVERT(nvarchar(max), a.[Note])),
    ('OE Number',          CONVERT(nvarchar(max), a.[OE Number])),
    ('Split Year',         CONVERT(nvarchar(max), a.[Split Year]))
) AS s(MatchColumn, MatchValue)
CROSS APPLY (VALUES (
    LTRIM(RTRIM(s.MatchValue)) COLLATE Latin1_General_100_BIN2
)) AS c(CleanValue)
INNER JOIN #QdbImpactNotes AS n
    ON n.NoteHash = CONVERT(binary(32), HASHBYTES('SHA2_256', c.CleanValue))
   AND n.NoteText = c.CleanValue
WHERE c.CleanValue IS NOT NULL AND c.CleanValue <> N'';

CREATE UNIQUE CLUSTERED INDEX IX_QdbImpactCells_Key
ON #QdbImpactCells (NoteId, VioRowId, MatchColumn);

-- A note matching several columns on one row contributes one row, several cells.
SELECT NoteId, VioRowId, COUNT_BIG(*) AS MatchedCellCount
INTO #QdbImpactNoteRows
FROM #QdbImpactCells
GROUP BY NoteId, VioRowId;

CREATE UNIQUE CLUSTERED INDEX IX_QdbImpactNoteRows_Key
ON #QdbImpactNoteRows (NoteId, VioRowId);

-- Across the complete mapped list, count each VIO row only once.
SELECT r.VioRowId, SUM(r.MatchedCellCount) AS MappedCellCount
INTO #QdbImpactCoveredRows
FROM #QdbImpactNoteRows AS r
INNER JOIN #QdbImpactNotes AS n ON n.NoteId = r.NoteId
WHERE n.IsMapped = 1
GROUP BY r.VioRowId;

CREATE UNIQUE CLUSTERED INDEX IX_QdbImpactCoveredRows_Id
ON #QdbImpactCoveredRows (VioRowId);

-- Retain descriptions with no match to any imported note.
SELECT
    IDENTITY(int, 1, 1) AS DescriptionId,
    [Description]
INTO #QdbImpactDescriptions
FROM (SELECT DISTINCT [Description] FROM #QdbImpactVio) AS d;

-- Prioritization metric: every matching cell in each description for ALL report notes.
SELECT v.[Description], COUNT_BIG(*) AS PotentialCells
INTO #QdbImpactDescriptionPotential
FROM #QdbImpactCells AS c
INNER JOIN #QdbImpactVio AS v ON v.VioRowId = c.VioRowId
GROUP BY v.[Description];

-- Each detail count and column list is specific to its note AND description.
SELECT
    r.NoteId,
    v.[Description],
    COUNT_BIG(*) AS MatchedVioRowCount,
    SUM(r.MatchedCellCount) AS MatchedCellCount
INTO #QdbImpactNoteDescriptions
FROM #QdbImpactNoteRows AS r
INNER JOIN #QdbImpactVio AS v ON v.VioRowId = r.VioRowId
GROUP BY r.NoteId, v.[Description];

CREATE INDEX IX_QdbImpactNoteDescriptions_NoteId ON #QdbImpactNoteDescriptions (NoteId);

-- The preceding table has one row per note and description, including NULL groups.
SELECT NoteId, COUNT_BIG(*) AS DescriptionCount
INTO #QdbImpactNoteStats
FROM #QdbImpactNoteDescriptions
GROUP BY NoteId;

CREATE UNIQUE CLUSTERED INDEX IX_QdbImpactNoteStats_Id ON #QdbImpactNoteStats (NoteId);

SELECT
    NoteId,
    [Description],
    STRING_AGG(CONVERT(nvarchar(max), MatchColumn), N'; ')
        WITHIN GROUP (ORDER BY MatchColumn) AS MatchedColumns
INTO #QdbImpactNoteDescriptionColumns
FROM (
    SELECT DISTINCT c.NoteId, v.[Description], c.MatchColumn
    FROM #QdbImpactCells AS c
    INNER JOIN #QdbImpactVio AS v ON v.VioRowId = c.VioRowId
) AS d
GROUP BY NoteId, [Description];

CREATE INDEX IX_QdbImpactNoteDescriptionColumns_NoteId
ON #QdbImpactNoteDescriptionColumns (NoteId);

-- RESULT 1: Current mapped-note impact and potential impact of the entire list.
-- Completion covers the entire combined list, including notes with no VIO match.
;WITH ListTotals AS (
    SELECT
        COUNT_BIG(*) AS TotalNotes,
        SUM(CAST(IsMapped AS bigint)) AS MappedNotes
    FROM #QdbImpactNotes
), CoveredTotals AS (
    SELECT
        COUNT_BIG(*) AS CoveredRows,
        COALESCE(SUM(r.MappedCellCount), CAST(0 AS bigint)) AS MatchedCells,
        COUNT_BIG(DISTINCT v.[Description])
            + COALESCE(MAX(CAST(CASE WHEN v.[Description] IS NULL
                                    THEN 1 ELSE 0 END AS bigint)), 0) AS Descriptions
    FROM #QdbImpactCoveredRows AS r
    INNER JOIN #QdbImpactVio AS v ON v.VioRowId = r.VioRowId
), VioTotals AS (
    SELECT COUNT_BIG(*) AS TotalVioRows FROM #QdbImpactVio
), AllListedNoteTotals AS (
    -- Include both mapped and unmapped notes; count shared VIO rows once.
    SELECT COUNT_BIG(DISTINCT VioRowId) AS PotentialRows
    FROM #QdbImpactNoteRows
), AllListedDescriptionTotals AS (
    -- Count each matching description once across the complete note list.
    SELECT COUNT_BIG(*) AS PotentialDescriptions
    FROM (SELECT DISTINCT [Description] FROM #QdbImpactNoteDescriptions) AS d
)
SELECT
    v.TotalVioRows AS [Total VIO Rows Searched],
    l.TotalNotes AS [Total Unique Notes In Combined QDB Mapping List],
    l.MappedNotes AS [Notes Marked Mapped],
    CAST(100.0 * l.MappedNotes / NULLIF(l.TotalNotes, 0) AS decimal(6, 2))
        AS [Combined List Mapping Completion Percent],
    c.MatchedCells AS [Cells Containing Mapped Notes],
    c.CoveredRows AS [Unique VIO Rows Containing Mapped Notes],
    CAST(100.0 * c.CoveredRows / NULLIF(v.TotalVioRows, 0) AS decimal(6, 2))
        AS [Percent Of All VIO Rows Affected],
    c.Descriptions AS [Descriptions Containing Mapped Notes],
    a.PotentialRows AS [Unique VIO Rows Affected If All Notes In Combined QDB Mapping List Were Mapped],
    CAST(100.0 * a.PotentialRows / NULLIF(v.TotalVioRows, 0) AS decimal(6, 2))
        AS [Percent Of All VIO Rows Affected If All Notes In Combined QDB Mapping List Were Mapped],
    d.PotentialDescriptions AS [Unique Descriptions Affected If All Notes In Combined QDB Mapping List Were Mapped]
FROM ListTotals AS l
CROSS JOIN CoveredTotals AS c
CROSS JOIN VioTotals AS v
CROSS JOIN AllListedNoteTotals AS a
CROSS JOIN AllListedDescriptionTotals AS d;

-- RESULT 2: Selected detail columns plus potential matching cells for each description.
SELECT
    CASE
        WHEN n.NoteId IS NULL THEN 'Description With No Match To Combined QDB Mapping List Notes'
        WHEN nd.NoteId IS NULL THEN 'Note With No VIO Match'
        ELSE 'Note Found In Description'
    END AS [Report Row Type],
    CASE WHEN d.DescriptionId IS NOT NULL
         THEN COALESCE(d.[Description], '(No description)') END AS [VIO Description],
    CASE WHEN d.DescriptionId IS NOT NULL THEN COALESCE(p.PotentialCells, CAST(0 AS bigint)) END
        AS [This Description - Matching Cells If All Combined QDB Mapping List Notes Were Mapped],
    n.NoteText AS [Searched Note],
    ng.NoteGroups AS [Note Group],
    CASE WHEN n.NoteId IS NULL THEN NULL
         WHEN n.IsMapped = 1 THEN 'Mapped' ELSE 'Not Mapped' END AS [Mapping Status],
    CASE WHEN n.NoteId IS NULL THEN NULL
         WHEN s.NoteId IS NULL THEN 'No VIO Match' ELSE 'Found In VIO' END AS [VIO Match Status],

    CASE WHEN n.NoteId IS NOT NULL THEN COALESCE(nd.MatchedCellCount, CAST(0 AS bigint)) END
        AS [This Note In This Description - Matching Cells],
    CASE WHEN n.NoteId IS NOT NULL THEN COALESCE(nd.MatchedVioRowCount, CAST(0 AS bigint)) END
        AS [This Note In This Description - Unique Matching VIO Rows],
    CASE WHEN n.NoteId IS NOT NULL THEN COALESCE(dc.MatchedColumns, 'No VIO Match') END
        AS [This Note In This Description - Matching VIO Columns],

    CASE WHEN n.NoteId IS NOT NULL THEN COALESCE(s.DescriptionCount, CAST(0 AS bigint)) END
        AS [This Note Across All Descriptions - Number Of Descriptions]
FROM #QdbImpactNotes AS n
LEFT JOIN #QdbImpactNoteDescriptions AS nd ON nd.NoteId = n.NoteId
FULL OUTER JOIN #QdbImpactDescriptions AS d
    ON nd.NoteId IS NOT NULL
   AND (nd.[Description] = d.[Description]
        OR (nd.[Description] IS NULL AND d.[Description] IS NULL))
LEFT JOIN #QdbImpactNoteGroups AS ng ON ng.NoteId = n.NoteId
LEFT JOIN #QdbImpactNoteStats AS s ON s.NoteId = n.NoteId
LEFT JOIN #QdbImpactDescriptionPotential AS p
    ON d.DescriptionId IS NOT NULL
   AND (p.[Description] = d.[Description]
        OR (p.[Description] IS NULL AND d.[Description] IS NULL))
LEFT JOIN #QdbImpactNoteDescriptionColumns AS dc
    ON dc.NoteId = nd.NoteId
   AND (dc.[Description] = nd.[Description]
        OR (dc.[Description] IS NULL AND nd.[Description] IS NULL))
ORDER BY
    CASE WHEN d.DescriptionId IS NULL THEN 1 ELSE 0 END,
    COALESCE(p.PotentialCells, 0) DESC,
    d.[Description], n.IsMapped DESC,
    COALESCE(nd.MatchedVioRowCount, 0) DESC, n.NoteText;

-- Release temporary storage. Run the entire file again for a fresh report.
DROP TABLE #QdbImpactNoteDescriptionColumns;
DROP TABLE #QdbImpactNoteDescriptions;
DROP TABLE #QdbImpactDescriptions;
DROP TABLE #QdbImpactDescriptionPotential;
DROP TABLE #QdbImpactNoteStats;
DROP TABLE #QdbImpactCoveredRows;
DROP TABLE #QdbImpactNoteRows;
DROP TABLE #QdbImpactCells;
DROP TABLE #QdbImpactVio;
DROP TABLE #QdbImpactNoteGroups;
DROP TABLE #QdbImpactNotes;
DROP TABLE #QdbImpactDistinctNotes;
DROP TABLE #QdbImpactInput;

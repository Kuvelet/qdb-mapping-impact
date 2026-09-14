"""Reference arithmetic, not a replacement for SQL Server's production pipeline."""

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP


SEARCH_COLUMNS = (
    "BodyStyle", "BrakeType", "CarbNumber", "CarbType", "Color",
    "Connection Type", "Cylinder Head Type", "Emissions", "FootNote",
    "Lead Length", "Note", "OE Number", "Split Year",
)

SUMMARY_HEADERS = (
    "Total VIO Rows Searched",
    "Total Unique Notes Present In Low Confidence QDB Report",
    "Notes Marked Mapped",
    "Project Completion Percent",
    "Cells Containing Mapped Notes",
    "Unique VIO Rows Containing Mapped Notes",
    "Percent Of All VIO Rows Affected",
    "Descriptions Containing Mapped Notes",
    "Unique VIO Rows Affected If All Unique Notes Present In Low Confidence QDB Report Were Mapped",
    "Percent Of All VIO Rows Affected If All Unique Notes Present In Low Confidence QDB Report Were Mapped",
    "Unique Descriptions Affected If All Unique Notes Present In Low Confidence QDB Report Were Mapped",
)

DETAIL_HEADERS = (
    "Report Row Type", "VIO Description",
    "This Description - Matching Cells If All Low Confidence QDB Report Notes Were Mapped",
    "Searched Note", "Mapping Status", "VIO Match Status",
    "This Note In This Description - Unique Matching VIO Rows",
    "This Note In This Description - Matching VIO Columns",
    "This Note Across All Descriptions - Number Of Descriptions",
)


def clean(value):
    """Match SQL LTRIM/RTRIM: remove ordinary spaces, not tabs or newlines."""
    if value is not None and not isinstance(value, str):
        raise ValueError("Inputs must be strings or null; convert source values in the adapter.")
    return value.strip(" ") if value is not None else None


def percent(numerator, denominator):
    if not denominator:
        return None
    return float((Decimal(100) * numerator / denominator).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    ))


def analyze(note_records, applications):
    """Return summary and detail dictionaries using exact, case-sensitive matches.

    Every input application record is a distinct row, even when values repeat.
    This models logical results only; it does not emulate SQL query plans,
    isolation, all Unicode collation ordering, or engine resource behavior.
    """
    notes = {}
    for record in note_records:
        note = clean(record.get("Note"))
        status = (clean(record.get("MappingStatus")) or "").upper()
        if not note:
            raise ValueError("Blank Note is not allowed.")
        if status not in ("", "MAPPED"):
            raise ValueError("MappingStatus must be Mapped or blank/null.")
        mapped = status == "MAPPED"
        if note in notes and notes[note] != mapped:
            raise ValueError("Conflicting mapping statuses for the same cleaned note.")
        notes[note] = mapped
    if not notes:
        raise ValueError("The mapping input is empty.")

    applications = list(applications)
    descriptions = [clean(a.get("Description")) or None for a in applications]
    cells = []
    for row_id, application in enumerate(applications):
        for column in SEARCH_COLUMNS:
            value = clean(application.get(column))
            if value in notes:
                cells.append((value, row_id, column))

    note_description_rows = defaultdict(set)
    note_description_columns = defaultdict(set)
    note_descriptions = defaultdict(set)
    description_cells = defaultdict(int)
    for note, row_id, column in cells:
        description = descriptions[row_id]
        key = (note, description)
        note_description_rows[key].add(row_id)
        note_description_columns[key].add(column)
        note_descriptions[note].add(description)
        description_cells[description] += 1

    mapped_cells = [(n, r, c) for n, r, c in cells if notes[n]]
    mapped_rows = {r for _, r, _ in mapped_cells}
    potential_rows = {r for _, r, _ in cells}
    mapped_descriptions = {descriptions[r] for r in mapped_rows}
    potential_descriptions = {descriptions[r] for r in potential_rows}
    total_mapped = sum(notes.values())
    summary = dict(zip(SUMMARY_HEADERS, (
        len(applications), len(notes), total_mapped, percent(total_mapped, len(notes)),
        len(mapped_cells), len(mapped_rows), percent(len(mapped_rows), len(applications)),
        len(mapped_descriptions), len(potential_rows),
        percent(len(potential_rows), len(applications)), len(potential_descriptions),
    )))

    detail = []
    for note, mapped in notes.items():
        if not note_descriptions[note]:
            values = (
                "Note With No VIO Match", None, None, note,
                "Mapped" if mapped else "Not Mapped", "No VIO Match", 0,
                "No VIO Match", 0,
            )
            detail.append(dict(zip(DETAIL_HEADERS, values)))
        for description in note_descriptions[note]:
            key = (note, description)
            values = (
                "Note Found In Description", description, description_cells[description],
                note, "Mapped" if mapped else "Not Mapped", "Found In VIO",
                len(note_description_rows[key]),
                "; ".join(sorted(note_description_columns[key])),
                len(note_descriptions[note]),
            )
            detail.append(dict(zip(DETAIL_HEADERS, values)))
    for description in set(descriptions) - potential_descriptions:
        values = (
            "Description With No Match To Low Confidence QDB Report Notes",
            description, 0, None, None, None, None, None, None,
        )
        detail.append(dict(zip(DETAIL_HEADERS, values)))

    detail.sort(key=lambda row: (
        row[DETAIL_HEADERS[0]] == "Note With No VIO Match",
        -(row[DETAIL_HEADERS[2]] or 0), row[DETAIL_HEADERS[1]] or "",
        row[DETAIL_HEADERS[4]] != "Mapped", -(row[DETAIL_HEADERS[6]] or 0),
        row[DETAIL_HEADERS[3]] or "",
    ))
    return {"summary": summary, "detail": detail}

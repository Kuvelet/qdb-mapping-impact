"""Local preflight and explicit execution controls; no browser operations here."""

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4


REQUIRED_COLUMNS = {
    "no-parameter": ("Note", "QDB Text"),
    "single-parameter": ("Note", "QDB Text", "Note Parameters"),
    "dual-parameter": ("Note", "QDB Text", "Note1 Parameter", "Note2 Parameter"),
}


@dataclass(frozen=True)
class Settings:
    mode: str
    input_path: Path
    url: str | None
    start_row: int
    limit: int
    output_dir: Path
    execute: bool


def parse_settings(mode, argv=None):
    if mode not in REQUIRED_COLUMNS:
        raise ValueError("Unknown mapping mode.")
    parser = argparse.ArgumentParser(
        description=f"{mode} PIM mapping automation. Default: local workbook preview only."
    )
    parser.add_argument("--input", type=Path, required=True, help="Authorized Excel mapping instructions.")
    parser.add_argument("--start-row", type=int, default=2, help="Excel row number; row 1 is the header.")
    parser.add_argument("--limit", type=int, default=1, help="Maximum input rows, including skipped rows (default: 1).")
    parser.add_argument("--url", help="Explicit authorized PIM URL; no embedded credentials.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/automation"))
    parser.add_argument("--execute", action="store_true", help="Enable live browser actions; replaces existing mappings.")
    parser.add_argument("--allow-mapping-replacement", action="store_true", help="Acknowledge the Remove Mapping action and lack of rollback.")
    parser.add_argument("--allow-insecure-http", action="store_true", help="Explicitly permit an authorized legacy HTTP endpoint.")
    args = parser.parse_args(argv)
    if args.start_row < 2:
        parser.error("--start-row must be at least 2.")
    if args.limit < 1:
        parser.error("--limit must be positive.")
    if not args.input.is_file() or args.input.suffix.lower() != ".xlsx":
        parser.error("--input must identify an existing .xlsx file.")
    if args.execute and not args.allow_mapping_replacement:
        parser.error("Live execution requires --allow-mapping-replacement; removal is not transactional.")
    if args.execute and not args.url:
        parser.error("Live execution requires an explicit --url.")
    if args.url:
        try:
            url = urlsplit(args.url)
            valid_url = bool(url.hostname) and url.scheme in ("https", "http")
            if not valid_url or url.username or url.password or url.query or url.fragment:
                parser.error("Use an HTTP(S) URL without credentials, query, or fragment.")
        except ValueError:
            parser.error("Invalid --url.")
        if args.execute and url.scheme == "http" and not args.allow_insecure_http:
            parser.error("HTTP is not encrypted. Prefer HTTPS; legacy HTTP requires --allow-insecure-http.")
    return Settings(mode, args.input.resolve(), args.url, args.start_row, args.limit,
                    args.output_dir.resolve(), args.execute)


def validate_headers(columns, mode):
    columns = list(columns)
    missing = sorted(set(REQUIRED_COLUMNS[mode]) - set(columns))
    if missing:
        raise ValueError("Missing required workbook columns: " + ", ".join(missing))
    if len(set(columns)) != len(columns):
        raise ValueError("Duplicate workbook headers are not supported.")


def selected_row_count(total_rows, start_row, limit):
    return min(limit, max(0, total_rows - (start_row - 2)))


def load_workbook(settings):
    # Keep Excel dependencies out of imports and --help, and inspect before Chrome starts.
    import pandas as pd
    raw = pd.read_excel(settings.input_path, header=None, nrows=1)
    validate_headers(raw.iloc[0].tolist() if len(raw) else [], settings.mode)
    frame = pd.read_excel(settings.input_path)
    validate_headers(frame.columns, settings.mode)
    return frame


def show_preview(settings, frame):
    selected = selected_row_count(len(frame), settings.start_row, settings.limit)
    print(f"Mode: {settings.mode}")
    print(f"Workbook data rows: {len(frame)}; selected rows: {selected}")
    print(f"Start Excel row: {settings.start_row}; limit: {settings.limit}")
    print("Required headers present. This preview does not validate every row's content or PIM state.")
    print("No browser opened, mappings changed, or report files written.")


def create_run_paths(settings):
    if not settings.execute:
        raise ValueError("Preview mode must not create execution outputs.")
    run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_" + uuid4().hex[:8]
    folder = settings.output_dir / f"{settings.mode}_{run_id}"
    folder.mkdir(parents=True, exist_ok=False)
    return folder / "automation_log.txt", folder / "mapping_report.csv"

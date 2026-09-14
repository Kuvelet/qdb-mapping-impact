"""Run the synthetic demo: python -m qdb_impact."""

import argparse
import json
from pathlib import Path

from .model import analyze


def table(headers, rows):
    def escape(value):
        if value is None:
            return "(null)"
        return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(escape(v) for v in row) + " |" for row in rows),
    ])


def main():
    parser = argparse.ArgumentParser(description="Run the synthetic Qdb impact example.")
    parser.add_argument("--input", type=Path, default=Path(__file__).resolve().parents[1] / "examples/synthetic_catalog.json")
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/demo"))
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    report = analyze(data["notes"], data["applications"])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    summary_table = table(["Metric", "Value"], report["summary"].items())
    detail = report["detail"]
    markdown = "# Synthetic Demo Results\n\nNot company data. Counts are illustrative.\n\n"
    markdown += summary_table + "\n\n## Detail\n\n"
    markdown += table(detail[0].keys(), [r.values() for r in detail]) + "\n"
    (args.out_dir / "report.md").write_text(markdown, encoding="utf-8")
    print(summary_table)
    print(f"\nWrote report.json and report.md to {args.out_dir.resolve()}")


if __name__ == "__main__":
    main()

"""Optional, explicit SQL Server smoke check. No default server or credentials."""

import argparse
from decimal import Decimal
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connection-string-env", default="QDB_SQL_CONNECTION_STRING")
    args = parser.parse_args()
    connection_string = os.environ.get(args.connection_string_env)
    if not connection_string:
        raise SystemExit("Set the named environment variable to an authorized SQL Server connection string. No connection was attempted.")
    try:
        import pyodbc
    except ImportError:
        raise SystemExit("Optional dependency missing: install pyodbc and a SQL Server ODBC driver.")
    expected = json.loads((ROOT / "examples/expected_report.json").read_text())
    with pyodbc.connect(connection_string, timeout=15, autocommit=True) as connection:
        cursor = connection.cursor()
        for file in ("00_demo_inputs.sql", "10_impact_report.sql"):
            cursor.execute((ROOT / "sql" / file).read_text(encoding="utf-8"))
            result_sets = []
            while True:
                if cursor.description:
                    names = [d[0] for d in cursor.description]
                    result_sets.append([
                        dict(zip(names, (float(v) if isinstance(v, Decimal) else v for v in row)))
                        for row in cursor.fetchall()
                    ])
                if not cursor.nextset():
                    break
    if len(result_sets) != 2 or result_sets[0] != [expected["summary"]]:
        raise SystemExit("FAIL: SQL Server summary does not match the synthetic reference.")
    serialize = lambda row: json.dumps(row, sort_keys=True)
    if sorted(map(serialize, result_sets[1])) != sorted(map(serialize, expected["detail"])):
        raise SystemExit("FAIL: SQL Server detail does not match the synthetic reference.")
    print("PASS: Both synthetic SQL Server result sets match the reference.")


if __name__ == "__main__":
    main()

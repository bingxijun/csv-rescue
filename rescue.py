"""CSV Rescue: explicit mapping, lossless string values, new outputs only.

Python 3.10+ standard library. No network, credentials or deletion operations.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys


def spreadsheet_cell(value):
    """Review-only mitigation; never used for the canonical import data."""
    stripped = value.lstrip()
    if stripped.startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


def prepare(source, rules):
    raw = source.read_bytes()
    mapping = rules.get("columns")
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError("columns must be a non-empty target-to-source object")
    if any(not isinstance(k, str) or not k or not isinstance(v, str) for k, v in mapping.items()):
        raise ValueError("column names must be non-empty strings")
    for option in ("trim", "required", "key"):
        values = rules.get(option, [])
        if not isinstance(values, list) or any(not isinstance(v, str) or v not in mapping for v in values):
            raise ValueError(f"{option} must be a list of target column names")
    delimiter = rules.get("delimiter", ",")
    if delimiter not in (",", ";", "\t", "|"):
        raise ValueError("delimiter must be comma, semicolon, tab or pipe")
    unknown = set(rules) - {"columns", "trim", "required", "key", "delimiter"}
    if unknown:
        raise ValueError("unknown configuration option: " + ", ".join(sorted(unknown)))
    reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), delimiter=delimiter, strict=True)
    headers = next(reader, None)
    if not headers or any(not header for header in headers):
        raise ValueError("input must contain non-empty headers")
    if len(set(headers)) != len(headers):
        raise ValueError("duplicate input headers")
    missing = set(mapping.values()) - set(headers)
    if missing:
        raise ValueError("unknown source column: " + ", ".join(sorted(missing)))
    indexes = [headers.index(name) for name in mapping.values()]
    targets = list(mapping)
    trim = set(rules.get("trim", []))
    required = rules.get("required", [])
    keys = rules.get("key", [])
    rows, changes, missing_required = [], [], []
    groups = {}
    for number, source_row in enumerate(reader, 1):
        if len(source_row) != len(headers):
            raise ValueError(f"record {number} has {len(source_row)} fields; expected {len(headers)}")
        row = [source_row[index] for index in indexes]
        for index, target in enumerate(targets):
            if target in trim:
                trimmed = row[index].strip()
                if trimmed != row[index]:
                    changes.append({"record": number, "column": target, "operation": "trim"})
                    row[index] = trimmed
        values = dict(zip(targets, row))
        for column in required:
            if not values[column].strip():
                missing_required.append({"record": number, "column": column})
        # Missing keys are not pooled into a misleading duplicate group.
        if keys and all(values[key].strip() for key in keys):
            key = tuple(values[column] for column in keys)
            groups.setdefault(key, []).append(number)
        rows.append(row)
    report = {
        "version": 1,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "rows_in": len(rows), "rows_out": len(rows),
        "source_columns": headers, "mapping": mapping,
        "unmapped_source_columns": [name for name in headers if name not in mapping.values()],
        "rules": rules,
        "changes": changes,
        "missing_required": missing_required,
        "duplicate_groups": [{"records": numbers} for numbers in groups.values() if len(numbers) > 1],
        "spreadsheet_review_escaped_cells": sum(spreadsheet_cell(value) != value for row in [targets, *rows] for value in row),
        "record_numbering": "1-based data records, excluding the header; not physical lines",
        "limitations": [
            "Duplicate and missing-value findings require review; no records were removed.",
            "Canonical data.csv retains formula-like strings. Do not open it directly in a spreadsheet.",
            "spreadsheet_review.csv prefixes formula-like text with apostrophes; CSV cannot enforce text typing or guarantee spreadsheet safety after re-saving.",
            "Import ID and price columns explicitly as text to preserve their display in spreadsheet applications.",
            "No target platform import or business-rule correctness is implied by these checks."
        ]
    }
    return targets, rows, report


def write_bundle(output, headers, rows, report):
    # mkdir(exist_ok=False) also prevents overwriting an empty pre-existing folder.
    output.mkdir(parents=True, exist_ok=False)
    for name, transform in (("data.csv", lambda value: value), ("spreadsheet_review.csv", spreadsheet_cell)):
        with (output / name).open("x", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle, quoting=csv.QUOTE_ALL)
            writer.writerow([transform(value) for value in headers])
            writer.writerows([transform(value) for value in row] for row in rows)
    with (output / "report.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    with (output / "QA.md").open("x", encoding="utf-8") as handle:
        handle.write("# CSV Rescue — QA summary\n\n")
        handle.write(f"Records: {report['rows_in']} input / {report['rows_out']} output.\n\n")
        handle.write(f"Explicit trim changes: {len(report['changes'])}.\n\n")
        handle.write(f"Duplicate key groups: {len(report['duplicate_groups'])}; missing required values: {len(report['missing_required'])}.\n\n")
        handle.write("Source SHA-256: `" + report["input_sha256"] + "`.\n\n")
        handle.write("Full mappings, changes and record numbers are in report.json.\n\n")
        handle.write("\n".join("- " + note for note in report["limitations"]) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New directory; existing paths are refused")
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("output already exists; choose a new directory")
        rules = json.loads(args.config.read_text(encoding="utf-8-sig"))
        if not isinstance(rules, dict):
            raise ValueError("configuration must be a JSON object")
        headers, rows, report = prepare(args.source, rules)
        write_bundle(args.output, headers, rows, report)
    except (OSError, ValueError, csv.Error, UnicodeError) as exc:
        print(f"CSV Rescue: {exc}", file=sys.stderr)
        return 2
    print(f"Created {args.output}: {len(rows)} records; review QA.md before import.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

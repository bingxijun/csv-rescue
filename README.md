# CSV Rescue

**Supplier export → explicit mapping → repeatable import files.**

A small, free, open-source Python tool for people who need to reshape a CSV without losing leading zeros, changing prices, or silently dropping records. No packages to install. No network calls. Your source file is read only; every run requires a new output directory.

## See a complete example

The [invented supplier export](examples/supplier.csv) contains SKU `0007`, price text `0012.50`, a duplicate SKU, a missing SKU and formula-like text. The [mapping](examples/mapping.json) renames three fields and trims only the product name.

| Before | After | Treatment |
| --- | --- | --- |
| Supplier SKU: `0007` | sku: `0007` | Exact string preserved |
| Price: `0012.50` | price: `0012.50` | No numeric conversion |
| Product Name: ` Blue, mug ` | name: `Blue, mug` | Only the explicitly selected field is trimmed |
| Duplicate SKU | Both rows retained | Flagged in the report |
| Missing SKU | Row retained | Flagged for review |
| `=2+2` | Same in canonical data | Separate review copy prefixes an apostrophe |

View the actual [QA summary](examples/result/QA.md) and [machine-readable report](examples/result/report.json). This is a demonstration, not customer work or a testimonial.

## Run locally

Requires Python 3.10 or newer. No `pip install` or account needed.

```sh
python rescue.py examples/supplier.csv --config examples/mapping.json --output my-new-result
python -m unittest -v
```

Configuration maps **target → source** column names:

```json
{
  "columns": {"sku": "Supplier SKU", "name": "Product Name", "price": "Price"},
  "trim": ["name"],
  "required": ["sku"],
  "key": ["sku"]
}
```

Optional `delimiter`: comma (default), semicolon, tab or pipe. Inputs must be UTF-8, optionally with a BOM. Field and header names are case-sensitive. Only mapped columns are exported; the report lists unmapped source columns. Key comparisons are exact after explicitly configured trimming. Missing keys are flagged by `required`, not grouped as duplicates. Validation findings do not remove rows or make the CLI fail; parse/configuration errors do fail before outputs are created.

Each bundle contains:

- `data.csv`: canonical strings for machine import. May contain formula-like values; do not double-click it in Excel.
- `spreadsheet_review.csv`: review copy with apostrophe prefixes on formula-like cells and headers. This changes those strings and is not the canonical import file.
- `report.json`: source SHA-256, mappings, unmapped columns, record counts, exact trim locations, missing values and duplicate groups.
- `QA.md`: concise handoff summary and limitations.

CSV cannot force spreadsheet text types. When using a spreadsheet import dialog, explicitly import identifier and price columns as **text**. Apostrophe prefixing reduces formula interpretation on the first import but is not a guarantee across spreadsheet programs or after re-saving. No schema, store import or business correctness is inferred from the QA checks. Blank records and ragged rows are rejected rather than silently skipped. On an I/O error, partial output files may remain in the new directory; no automatic cleanup deletes them.

## Want this configured for your workflow?

The software above is free under the MIT license. Paid work is for agreeing and configuring your mappings, running acceptance checks, and delivering a reusable workflow.

| Service | Proposed fixed price | Included scope |
| --- | --- | --- |
| One-file mapping | US$39 | One UTF-8 CSV, up to 5,000 records / 20 columns / 5 MiB; column mapping, selected text trimming, required-field and exact-key duplicate report |
| Repeatable import setup | US$129 | Up to 3 agreed input layouts, 30,000 records total / 30 columns each / 10 MiB total; configured mappings, repeatable script, sample runs, exception report and usage notes |

One revision within the agreed mapping scope. Planned turnaround is within 24 hours **after** scope, permitted data handling, payment method and availability are confirmed. No live store access, credential handling, OCR, fuzzy matching, tax/accounting advice or guaranteed platform import success is included. Custom split/merge logic requires a separate quote.

**AI-assisted development and delivery.** Public code and synthetic samples can be reviewed freely. Do not upload customer records, personal information, confidential data or credentials into a public issue. Any processing of customer data needs an agreed private channel and permission first.

[Request a scope check](https://github.com/bingxijun/csv-rescue/issues/new?template=scope-check.yml) using only file type, approximate size, column names with invented values and your desired result. An inquiry is non-binding. Payment is not enabled in this repository; no order is accepted until payment arrangements and final terms are confirmed. No payment card is required to try the free tool.

## License

MIT; see [LICENSE](LICENSE). Service work is separate from the free software license.

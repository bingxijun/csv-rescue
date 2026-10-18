# CSV Rescue — QA summary

Records: 3 input / 3 output.

Explicit trim changes: 1.

Duplicate key groups: 1; missing required values: 1.

Source SHA-256: `2cf83721210f7fe32dee3fa6e12d92d3a56dc1bcf68e10d91f070db4a8029593`.

Full mappings, changes and record numbers are in report.json.

- Duplicate and missing-value findings require review; no records were removed.
- Canonical data.csv retains formula-like strings. Do not open it directly in a spreadsheet.
- spreadsheet_review.csv prefixes formula-like text with apostrophes; CSV cannot enforce text typing or guarantee spreadsheet safety after re-saving.
- Import ID and price columns explicitly as text to preserve their display in spreadsheet applications.
- No target platform import or business-rule correctness is implied by these checks.

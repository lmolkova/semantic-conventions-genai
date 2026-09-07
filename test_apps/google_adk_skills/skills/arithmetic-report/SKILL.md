---
name: arithmetic-report
description: Add two integers with a bundled deterministic script and report its output.
metadata:
  adk_additional_tools:
    - format_sum
---

# Arithmetic report

When asked to add two integers:

1. Run `scripts/add.py` with the two integers as positional arguments.
2. Return the script's exact stdout.

Do not calculate the result yourself.

When asked about output formatting, read `references/output-format.md`.
When asked for a report template, read `assets/report-template.txt`.

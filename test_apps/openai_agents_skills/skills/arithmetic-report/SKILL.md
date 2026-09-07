---
name: arithmetic-report
description: Add two integers with a bundled deterministic script and report its output.
---

# Arithmetic report

When asked to add two integers:

1. Run `scripts/add.py` with the two integers as positional arguments.
2. Return the script's exact stdout.

Do not calculate the result yourself.

For an interactive request, start `scripts/interactive_add.py` with a short
yield time, then send the two integers to the returned process session.

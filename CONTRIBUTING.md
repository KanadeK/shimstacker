# Contributing

Thank you for helping make small-shop allocation evidence more reliable.

## Before opening code

For a bug, reduce the problem to the smallest strict JSON plan and state the observed outcome, expected outcome, and reasoning. Remove private equipment and customer identifiers. For a feature, describe the real shop-floor decision and why the existing input cannot express it.

## Development setup

```console
git clone https://github.com/KanadeK/shimstacker.git
cd shimstacker
uv sync --extra dev --locked
uv run python scripts/check.py
```

The project supports Python 3.11-3.13 and has no runtime dependencies.

## Change rules

- Add a failing test before changing parser, solver, or exit-code behavior.
- Preserve `Decimal` arithmetic for authored dimensions.
- Never convert a bounded-search interruption into `infeasible`.
- Keep JSON as the single plan authority and `SolveResult` as the single report authority.
- Do not add heuristics, fallbacks, networking, or inventory mutation to hide an unsupported requirement.
- Update `docs/SPEC.md` when a public contract intentionally changes.

Run the full gate before submitting. A green unit test alone is not enough: packaging and the installed demo are part of the product.


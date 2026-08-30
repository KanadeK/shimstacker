# Project rules

- Keep the runtime dependency-free and offline.
- Treat the JSON plan as the only source of truth.
- Never report an incomplete search as infeasible.
- Represent authored dimensions with `decimal.Decimal`; do not use binary floats.
- Add a failing test before changing solver behavior.
- Keep generated reports deterministic and script-free.


# Architecture

ShimStacker has one forward-only authority path:

```text
authored JSON
    │ strict parse + Decimal model
    ▼
per-job complete combination enumeration
    │ guaranteed worst-case bands only
    ▼
global bounded backtracking over shared quantities
    │ exact objective and stable tie-break
    ▼
SolveResult: feasible | infeasible | indeterminate
    │ one immutable result
    ├── JSON evidence
    ├── CSV pick list
    ├── Markdown bench sheet
    └── standalone HTML report
```

## Modules

- `model.py` owns immutable validated values.
- `parse.py` is the only authored-input boundary. It rejects ambiguity rather than normalizing it silently.
- `solver.py` enumerates combinations and chooses the globally best allocation. The same state budget covers enumeration and allocation search.
- `reports.py` renders every artifact from one `Plan` and one `SolveResult`; reports do not recalculate feasibility.
- `cli.py` maps file boundaries and outcome-specific exit codes.

There is no legacy solver, fallback heuristic, cache, database, or second source of truth.

## Exactness and termination

Per-job enumeration walks count vectors bounded by each batch quantity and the job's `max_pieces`. It discards any vector whose summed minimum already exceeds the job's target maximum, because adding positive-thickness shims cannot recover it.

Global search orders jobs by candidate count to find constraints early, but the final objective is independent of that traversal order. It exhausts all non-pruned allocations before returning `infeasible` or declaring the best feasible allocation. If the shared `max_states` budget is consumed first, an internal limit signal becomes public `SHS199 indeterminate`; no partial plan is presented as approved.

## Determinism

Stock and job IDs are sorted at decision boundaries. The objective key is total piece count, total absolute midpoint deviation, then the full stable allocation signature. Reports contain no clock, random value, absolute source path, or network resource. The release gate produces two report bundles and compares every byte.

## Report publication

All four files are written to a staging directory beside the requested output. Only after rendering succeeds is that directory renamed into place. Existing output paths are rejected. A rendering or I/O failure removes the staging directory and preserves any existing user path.


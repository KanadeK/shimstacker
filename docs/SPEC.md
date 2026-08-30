# ShimStacker v0.1.0 specification

Status: frozen for implementation on 2026-08-30.

## Product outcome

ShimStacker is an offline command-line compiler for a small but consequential
shop-floor problem: allocate a finite shared stock of measured shim batches to
multiple assembly gaps, while proving that every resulting stack remains inside
its target band under worst-case stated tolerances.

It produces a pickable allocation and deterministic evidence. It does not
measure parts, infer material suitability, approve an assembly, or replace the
equipment manufacturer's procedure and a qualified technician's final
measurement.

## Facts, inference, and unknowns

### Confirmed

- Public tools exist for one-off required-thickness arithmetic and ordinary 1D
  tolerance-chain analysis.
- A commercial mobile app advertises local shim combinations, stock quantities,
  and tolerance hints.
- The GitHub repository searches recorded in `RESEARCH.md` returned no project
  focused on exact multi-job allocation from one finite shim inventory with
  worst-case proof and machine-readable infeasibility evidence.
- No current local project under `D:\我的\GitHub` addresses shim allocation.

### Inference

The useful open-source gap is not another calculator. It is a reviewable batch
planner that prevents the same scarce shim from being promised to two assemblies
and refuses to call a nominally close stack guaranteed.

### Unknown

Search cannot prove that no similar implementation exists anywhere. The claim is
limited to the documented queries and results checked on 2026-08-30.

## Authoritative input

One UTF-8 JSON file with these exact top-level fields:

```json
{
  "schema_version": 1,
  "project": "Gearbox rebuild",
  "unit": "mm",
  "max_states": 200000,
  "stock": [
    {
      "id": "S-010",
      "thickness": "0.10",
      "tolerance": "0.005",
      "quantity": 4
    }
  ],
  "jobs": [
    {
      "id": "input-bearing",
      "target_min": "0.285",
      "target_max": "0.315",
      "max_pieces": 3
    }
  ]
}
```

Decimal dimensions are JSON strings and are parsed with `decimal.Decimal`.
Unknown fields, duplicate IDs, booleans in integer fields, non-positive
thicknesses, negative tolerances, invalid ranges, unsafe CSV-leading unit labels,
and values beyond the explicit bounds fail validation. Units are labels only;
v0.1.0 performs no conversion.

Bounds: 1-32 stock batches, 1-24 jobs, quantity 1-100 per batch,
`max_pieces` 1-8 per job, and `max_states` 1-2,000,000.

## Solver contract

For a combination with nominal thicknesses `t` and stated symmetric tolerances
`e`:

```text
stack_min = sum(t - e)
stack_nominal = sum(t)
stack_max = sum(t + e)
```

A combination guarantees a job only when:

```text
target_min <= stack_min and stack_max <= target_max
```

The solver enumerates every bounded per-job combination, then performs an exact
global allocation without exceeding any stock quantity. Among feasible global
plans it chooses, in order:

1. the fewest total pieces;
2. the smallest total absolute nominal deviation from target midpoints;
3. the lexicographically smallest stable allocation signature.

The outcome is exactly one of:

- `feasible`: every job is allocated and proven inside its band;
- `infeasible`: the bounded search was exhausted, with diagnostics;
- `indeterminate`: `max_states` stopped the search before proof.

Diagnostics distinguish at least:

- `SHS101`: one job has no individually valid stack even with the full stock;
- `SHS102`: every job is individually possible, but shared stock cannot satisfy
  all jobs together;
- `SHS199`: the state limit prevented a conclusion.

## CLI and exit codes

```text
shimstacker validate PLAN.json
shimstacker plan PLAN.json --output REPORT_DIR
shimstacker demo --output REPORT_DIR
shimstacker --version
```

- `0`: valid input or feasible plan;
- `1`: proven infeasible plan;
- `2`: invalid input, usage, or I/O failure;
- `3`: indeterminate search.

`plan` creates a new output directory atomically and refuses to overwrite an
existing path. It writes `report.json`, `pick-list.csv`, `bench-sheet.md`, and a
self-contained, script-free `report.html` for all solver outcomes.

## Non-goals

- material, corrosion, temperature, compression, wear, or fastener engineering;
- statistical/RSS tolerance analysis;
- camera or gauge integration;
- automatic purchasing or inventory mutation;
- cloud storage, accounts, telemetry, or a browser application;
- unbounded industrial optimization.

## Acceptance criteria

- strict parser tests cover every boundary class;
- solver tests prove local combinations, global scarcity, deterministic
  tie-breaking, exhaustive infeasibility, and state-limit honesty;
- reports are byte-for-byte deterministic and escape authored text;
- a feasible and an infeasible example exercise the installed CLI;
- Ruff, strict mypy, branch coverage of at least 90%, package build, wheel
  inspection, and isolated wheel smoke tests pass on Python 3.11 and 3.13;
- GitHub CI, tagged release assets, and the static Pages demo are green;
- a fresh download/install/run reproduces the documented result.

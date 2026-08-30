# ShimStacker

[![CI](https://github.com/KanadeK/shimstacker/actions/workflows/ci.yml/badge.svg)](https://github.com/KanadeK/shimstacker/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/KanadeK/shimstacker)](https://github.com/KanadeK/shimstacker/releases/latest)
[![Pages](https://github.com/KanadeK/shimstacker/actions/workflows/pages.yml/badge.svg)](https://kanadek.github.io/shimstacker/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB)](https://www.python.org/)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Allocate the shims you actually own, then prove every stack still fits at its stated tolerance limits.**

[Live report](https://kanadek.github.io/shimstacker/) · [中文说明](README.zh-CN.md) · [Input reference](docs/INPUT.md) · [Why this is different](docs/RESEARCH.md)

ShimStacker is an offline, zero-runtime-dependency CLI for maintenance benches and small workshops. It solves all declared assembly gaps against one finite shared inventory. A shim cannot be promised to two jobs, and a nominally close stack does not pass unless its entire worst-case range stays inside the target band.

```text
FEASIBLE · 3/3 jobs allocated · 53 states · shim-report

flexible-bearing   1x B-200 + 1x C-100   0.294-0.306 mm   target 0.290-0.310
single-piece-seat  1x A-300               0.295-0.305 mm   target 0.290-0.310
thrust-cover       1x D-250               0.246-0.254 mm   target 0.245-0.255
```

The first job could take `A-300` by itself, but that would make the second job impossible. The exact global search leaves `A-300` for the single-piece seat and proves the two-piece alternative instead.

## Try it in 30 seconds

Python 3.11 or newer is required.

```console
python -m pip install https://github.com/KanadeK/shimstacker/releases/download/v0.1.0/shimstacker-0.1.0-py3-none-any.whl
shimstacker demo --output shim-report
```

Open `shim-report/report.html` or use the machine-readable files beside it:

| Artifact | Purpose |
| --- | --- |
| `report.json` | Complete outcome, allocations, inventory remaining, findings, and search evidence. |
| `pick-list.csv` | One row per stock batch picked for each job. |
| `bench-sheet.md` | Printable allocation and mandatory physical-verification reminder. |
| `report.html` | Responsive, standalone visual report with no scripts or remote assets. |

The CLI refuses to overwrite an existing report directory.

## Plan your own job

Create a UTF-8 JSON file. Dimensions are strings so decimal intent is preserved exactly.

```json
{
  "schema_version": 1,
  "project": "Gearbox rebuild",
  "unit": "mm",
  "max_states": 200000,
  "stock": [
    {"id": "S-010", "thickness": "0.10", "tolerance": "0.005", "quantity": 4},
    {"id": "S-020", "thickness": "0.20", "tolerance": "0.005", "quantity": 2}
  ],
  "jobs": [
    {"id": "input-bearing", "target_min": "0.285", "target_max": "0.315", "max_pieces": 3}
  ]
}
```

Then validate and solve it:

```console
shimstacker validate gearbox.json
shimstacker plan gearbox.json --output gearbox-report
```

For each candidate stack, ShimStacker computes:

```text
stack_min     = sum(thickness - tolerance)
stack_nominal = sum(thickness)
stack_max     = sum(thickness + tolerance)
```

It passes only when `target_min <= stack_min` and `stack_max <= target_max`. Feasible plans are ranked by fewest pieces, then midpoint deviation, then a stable ID tie-break. Every calculation uses Python `Decimal`, not binary floating point.

## Honest failure states

ShimStacker does not turn a timeout into a confident answer.

| Exit | Outcome | Meaning |
| ---: | --- | --- |
| `0` | `feasible` | Every job has a globally valid, quantity-safe allocation. |
| `1` | `infeasible` | The bounded search was exhausted and includes `SHS101` or `SHS102` evidence. |
| `2` | input/I/O error | The plan, path, or report request is invalid. |
| `3` | `indeterminate` | `max_states` stopped the search before proof (`SHS199`). |

Try the included conflict case:

```console
shimstacker plan src/shimstacker/examples/shared-stock-conflict.json --output conflict-report
# INFEASIBLE · SHS102: each job works alone, but both need the only 0.300 mm shim
```

## Boundaries that matter

ShimStacker proves arithmetic from declared nominal thicknesses, symmetric tolerances, target bands, quantities, and piece limits. It does **not** decide material compatibility, compression, corrosion, thermal behavior, fastener preload, wear, surface condition, or whether a machine is safe to operate. Follow the equipment manufacturer's procedure and have a qualified person measure the assembled result.

It never connects to equipment, mutates inventory, executes plan content, creates an account, or sends data over the network.

## Development

```console
git clone https://github.com/KanadeK/shimstacker.git
cd shimstacker
uv sync --extra dev --locked
uv run python scripts/check.py
```

The release gate runs formatting, linting, strict type checks, 90%+ branch coverage, both behavioral examples, deterministic-output comparison, package inspection, and an isolated wheel install. See [architecture](docs/ARCHITECTURE.md), [contributing](CONTRIBUTING.md), [security](SECURITY.md), and [troubleshooting](docs/TROUBLESHOOTING.md).

## License

MIT © 2026 KanadeK.


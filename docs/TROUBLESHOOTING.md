# Troubleshooting

## `output already exists`

ShimStacker never merges into or overwrites a report directory. Choose a new path or move the existing report yourself after reviewing it.

## `SHS101`

The named job has no combination that stays wholly inside its target band, even when considered with the full declared inventory. Check the target, measured nominal values, stated tolerances, and `max_pieces`. Adding inventory to a different thickness may be necessary.

## `SHS102`

Every job is possible by itself, but not at the same time with the declared quantities. Inspect the job IDs in `subjects` and the stock table. Do not solve jobs in separate plans unless their physical inventory is also separated; doing so can promise one shim twice.

## `SHS199`

The search reached `max_states` before proof. The result is deliberately neither success nor failure. Increase the limit within the supported maximum, reduce redundant stock batches, or tighten unrealistic `max_pieces` values. Merging batches is correct only when their thickness and tolerance are genuinely interchangeable.

## A nominal total fits but the plan is infeasible

Nominal fit is insufficient. The sum of every lower tolerance endpoint must stay above `target_min`, and the sum of every upper endpoint must stay below `target_max`.

## Decimal fields are rejected

Dimensions must be JSON strings such as `"0.125"`, not JSON numbers such as `0.125`. This prevents binary floating-point parsing from changing authored decimal intent.

## The installed `demo` cannot find its example

Run `shimstacker --version` and reinstall the official wheel. The release gate verifies that both JSON examples are package data and runs `demo` from an isolated virtual environment without the source checkout.


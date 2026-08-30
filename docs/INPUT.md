# Input reference

ShimStacker accepts one UTF-8 JSON object. Unknown and missing fields are errors; duplicate JSON object keys are rejected before model validation.

## Top-level fields

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | integer | Must be `1`. |
| `project` | string | 1-120 characters; used only as a report label. |
| `unit` | string | 1-16 characters with no surrounding/control whitespace or spreadsheet formula prefix. It is a label; no conversion occurs. Keep one unit throughout a plan. |
| `max_states` | integer | 1-2,000,000. A reached limit produces `indeterminate`, never `infeasible`. |
| `stock` | array | 1-32 unique stock batches. |
| `jobs` | array | 1-24 unique assembly jobs. |

## Stock batch

Each object has exactly `id`, `thickness`, `tolerance`, and `quantity`.

- `id`: stable identifier matching `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`.
- `thickness`: positive finite decimal string.
- `tolerance`: non-negative finite decimal string smaller than `thickness`.
- `quantity`: integer from 1 through 100. Pieces in one batch are treated as interchangeable.

Tolerance is symmetric. A `0.300` shim with `0.005` tolerance contributes `[0.295, 0.305]` to the worst-case stack interval.

## Job

Each object has exactly `id`, `target_min`, `target_max`, and `max_pieces`.

- `id`: unique stable identifier using the same syntax as stock IDs.
- `target_min`: non-negative finite decimal string.
- `target_max`: positive finite decimal string greater than `target_min`.
- `max_pieces`: integer from 1 through 8.

The target band is inclusive. A stack whose worst-case endpoints exactly equal the target endpoints passes.

## Limits

The fixed v0.1.0 bounds make exact search practical and reviewable. Split a larger shop list into independent plans when the inventory is genuinely independent. If inventory is shared, splitting changes the question and can double-promise stock; raise `max_states` instead or reduce unnecessary candidates.

# Differentiation research

Checked 2026-08-30. Search is evidence, not proof of universal absence.

## Local boundary

The current `D:\我的\GitHub` repository inventory was searched for `shim`,
`shim stack`, `shimstock`, and `tolerance stack`. No local project implements
finite shim-stock allocation. Related projects solve different problems, such as
cable routing, pottery kiln fit, luggage packing, and electrical load planning.

An earlier theatre quick-change candidate was discarded before publication when
the newly appeared local project `CueDresser` proved to be the same core idea.

## Public products and projects

| Project/product | What it does | Why ShimStacker is different |
| --- | --- | --- |
| EveryCalculators Shim Calculator | Computes one required thickness from a measured and target dimension. | No finite inventory or multi-job allocation. |
| EasyStackup | Open-source desktop 1D tolerance-chain analysis with worst-case and RSS output. | Analyzes design dimension loops; it does not allocate physical shim stock to shop jobs. |
| Shim Stack Tolerance Tool2026 | Commercial offline mobile combination calculator with a shim library, stock quantities, and tolerance hints. | Similar single-user product surface, but not an identified open-source GitHub project; ShimStacker's distinguishing contract is exact shared allocation, explicit exhaustive/indeterminate states, and deterministic CI evidence. |
| OptiStack Pro | Commercial coil-slitting tooling and spacer inventory planner. | Industry-specific arbor setup rather than general small shim packs. |

Sources:

- https://everycalculators.com/shim-calculator.html
- https://github.com/robertdosa/EasyStackup
- https://apps.apple.com/us/app/shim-stack-tolerance-tool2026/id6773656796
- https://www.optistackpro.com/

## GitHub repository queries

The connected GitHub repository search returned no repositories for:

- `shim stack calculator inventory tolerance`
- `shim selection optimizer`
- `shim pack thickness solver`
- `mechanical shim stack planner`

Exact candidate-name searches for `shimstacker`, `shimfit`, `shimforge`,
`gappack`, `shimwise`, and `shimplan` also returned no repositories.

## Decision

Proceed with `ShimStacker`. Do not claim it is the first shim calculator. Its
defensible novelty is the narrow conjunction of finite shared inventory,
worst-case decimal proof, exact bounded multi-job allocation, stable artifacts,
and honest infeasibility diagnostics.


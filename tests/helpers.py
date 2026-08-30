from __future__ import annotations

from typing import Any


def valid_plan_data() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "project": "Gearbox rebuild",
        "unit": "mm",
        "max_states": 200_000,
        "stock": [
            {"id": "S-010", "thickness": "0.10", "tolerance": "0.005", "quantity": 4},
            {"id": "S-020", "thickness": "0.20", "tolerance": "0.005", "quantity": 2},
        ],
        "jobs": [
            {
                "id": "input-bearing",
                "target_min": "0.285",
                "target_max": "0.315",
                "max_pieces": 3,
            }
        ],
    }

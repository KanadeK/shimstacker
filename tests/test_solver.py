from __future__ import annotations

import json

from shimstacker.parse import parse_plan_text
from shimstacker.solver import solve
from tests.helpers import valid_plan_data


def result_for(data):
    return solve(parse_plan_text(json.dumps(data)))


def allocation_parts(result, job_id: str) -> tuple[tuple[str, int], ...]:
    return next(item.parts for item in result.allocations if item.job_id == job_id)


def test_worst_case_interval_must_fit_entire_target_band() -> None:
    data = valid_plan_data()
    data["stock"] = [
        {"id": "wide", "thickness": "0.10", "tolerance": "0.006", "quantity": 3},
        {"id": "tight", "thickness": "0.10", "tolerance": "0.005", "quantity": 3},
    ]

    result = result_for(data)

    assert result.status == "feasible"
    assert allocation_parts(result, "input-bearing") == (("tight", 3),)
    allocation = result.allocations[0]
    assert str(allocation.stack_min) == "0.285"
    assert str(allocation.stack_max) == "0.315"


def test_minimizes_piece_count_before_midpoint_deviation() -> None:
    data = valid_plan_data()
    data["stock"] = [
        {"id": "single", "thickness": "0.305", "tolerance": "0", "quantity": 1},
        {"id": "half", "thickness": "0.15", "tolerance": "0", "quantity": 2},
    ]
    data["jobs"][0].update(target_min="0.29", target_max="0.31", max_pieces=2)

    result = result_for(data)

    assert allocation_parts(result, "input-bearing") == (("single", 1),)


def test_minimizes_deviation_then_uses_stable_id_tie_break() -> None:
    data = valid_plan_data()
    data["stock"] = [
        {"id": "z-near", "thickness": "0.301", "tolerance": "0", "quantity": 1},
        {"id": "a-near", "thickness": "0.299", "tolerance": "0", "quantity": 1},
        {"id": "far", "thickness": "0.306", "tolerance": "0", "quantity": 1},
    ]
    data["jobs"][0].update(target_min="0.29", target_max="0.31", max_pieces=1)

    result = result_for(data)

    assert allocation_parts(result, "input-bearing") == (("a-near", 1),)


def test_backtracks_across_jobs_instead_of_double_promising_stock() -> None:
    data = valid_plan_data()
    data["stock"] = [
        {"id": "A-300", "thickness": "0.30", "tolerance": "0", "quantity": 1},
        {"id": "B-200", "thickness": "0.20", "tolerance": "0", "quantity": 1},
        {"id": "C-100", "thickness": "0.10", "tolerance": "0", "quantity": 1},
    ]
    data["jobs"] = [
        {"id": "flexible", "target_min": "0.30", "target_max": "0.31", "max_pieces": 2},
        {"id": "single-only", "target_min": "0.30", "target_max": "0.31", "max_pieces": 1},
    ]

    result = result_for(data)

    assert result.status == "feasible"
    assert allocation_parts(result, "flexible") == (("B-200", 1), ("C-100", 1))
    assert allocation_parts(result, "single-only") == (("A-300", 1),)


def test_reports_individual_infeasibility_only_after_exhaustion() -> None:
    data = valid_plan_data()
    data["stock"] = [{"id": "S-100", "thickness": "0.10", "tolerance": "0", "quantity": 2}]
    data["jobs"][0].update(target_min="0.25", target_max="0.26", max_pieces=2)

    result = result_for(data)

    assert result.status == "infeasible"
    assert result.findings[0].code == "SHS101"
    assert result.findings[0].subjects == ("input-bearing",)


def test_reports_shared_inventory_conflict() -> None:
    data = valid_plan_data()
    data["stock"] = [{"id": "only-300", "thickness": "0.30", "tolerance": "0", "quantity": 1}]
    data["jobs"] = [
        {"id": "left", "target_min": "0.30", "target_max": "0.31", "max_pieces": 1},
        {"id": "right", "target_min": "0.30", "target_max": "0.31", "max_pieces": 1},
    ]

    result = result_for(data)

    assert result.status == "infeasible"
    assert result.findings[0].code == "SHS102"
    assert result.findings[0].subjects == ("left", "right")


def test_state_limit_is_indeterminate_not_infeasible() -> None:
    data = valid_plan_data()
    data["max_states"] = 1

    result = result_for(data)

    assert result.status == "indeterminate"
    assert result.findings[0].code == "SHS199"
    assert result.allocations == ()
    assert result.states_explored == 1


def test_input_order_does_not_change_allocation() -> None:
    data = valid_plan_data()
    data["stock"] = [
        {"id": "z", "thickness": "0.30", "tolerance": "0", "quantity": 1},
        {"id": "a", "thickness": "0.30", "tolerance": "0", "quantity": 1},
    ]
    data["jobs"][0].update(target_min="0.30", target_max="0.31", max_pieces=1)
    first = result_for(data)
    data["stock"].reverse()
    second = result_for(data)

    assert first.allocations == second.allocations
    assert allocation_parts(first, "input-bearing") == (("a", 1),)

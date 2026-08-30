from __future__ import annotations

import json
from decimal import Decimal

import pytest

from shimstacker.parse import PlanError, parse_plan_text
from tests.helpers import valid_plan_data


def encode(data: object) -> str:
    return json.dumps(data)


def test_parse_valid_plan_preserves_decimal_values() -> None:
    plan = parse_plan_text(encode(valid_plan_data()))

    assert plan.project == "Gearbox rebuild"
    assert plan.unit == "mm"
    assert plan.max_states == 200_000
    assert plan.stock[0].thickness == Decimal("0.10")
    assert plan.stock[0].minimum == Decimal("0.095")
    assert plan.jobs[0].midpoint == Decimal("0.300")


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: data.update(extra=True), "unknown field"),
        (lambda data: data.pop("project"), "missing field"),
        (lambda data: data.update(schema_version=True), "must be an integer"),
        (lambda data: data.update(schema_version=2), "must equal 1"),
        (lambda data: data.update(unit=""), "unit must not be empty"),
        (lambda data: data.update(max_states=0), "between 1 and 2000000"),
    ],
)
def test_rejects_invalid_top_level_fields(mutate, message: str) -> None:
    data = valid_plan_data()
    mutate(data)

    with pytest.raises(PlanError, match=message):
        parse_plan_text(encode(data))


@pytest.mark.parametrize("value", [0.1, 1, None, True, "NaN", "Infinity", "-0.1"])
def test_rejects_invalid_thickness(value: object) -> None:
    data = valid_plan_data()
    data["stock"][0]["thickness"] = value

    with pytest.raises(PlanError, match=r"stock\[0\]\.thickness"):
        parse_plan_text(encode(data))


def test_rejects_tolerance_not_smaller_than_thickness() -> None:
    data = valid_plan_data()
    data["stock"][0]["tolerance"] = "0.10"

    with pytest.raises(PlanError, match="must be smaller than thickness"):
        parse_plan_text(encode(data))


def test_rejects_duplicate_stock_and_job_ids() -> None:
    data = valid_plan_data()
    data["stock"].append(dict(data["stock"][0]))

    with pytest.raises(PlanError, match="duplicate stock id"):
        parse_plan_text(encode(data))

    data = valid_plan_data()
    data["jobs"].append(dict(data["jobs"][0]))

    with pytest.raises(PlanError, match="duplicate job id"):
        parse_plan_text(encode(data))


def test_rejects_invalid_job_range() -> None:
    data = valid_plan_data()
    data["jobs"][0]["target_min"] = "0.315"

    with pytest.raises(PlanError, match="target_max must be greater"):
        parse_plan_text(encode(data))


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("stock", 0, "quantity"), True, "must be an integer"),
        (("stock", 0, "quantity"), 101, "between 1 and 100"),
        (("jobs", 0, "max_pieces"), 9, "between 1 and 8"),
        (("jobs", 0, "id"), "bad id!", "invalid id"),
    ],
)
def test_rejects_invalid_nested_values(path, value: object, message: str) -> None:
    data = valid_plan_data()
    collection, index, field = path
    data[collection][index][field] = value

    with pytest.raises(PlanError, match=message):
        parse_plan_text(encode(data))


def test_rejects_duplicate_json_object_keys() -> None:
    text = encode(valid_plan_data()).replace(
        '"project": "Gearbox rebuild",',
        '"project": "First", "project": "Second",',
    )

    with pytest.raises(PlanError, match="duplicate object key: project"):
        parse_plan_text(text)


def test_rejects_invalid_json_and_non_object_root() -> None:
    with pytest.raises(PlanError, match="invalid JSON"):
        parse_plan_text("{")
    with pytest.raises(PlanError, match="root must be an object"):
        parse_plan_text("[]")


@pytest.mark.parametrize("unit", ["=1+1", "+SUM(A1)", "-2", "@name", "\tmm", "mm\n"])
def test_rejects_units_that_are_unsafe_in_csv(unit: str) -> None:
    data = valid_plan_data()
    data["unit"] = unit

    with pytest.raises(PlanError, match="unit contains unsafe characters"):
        parse_plan_text(encode(data))

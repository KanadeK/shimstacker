"""Strict parsing for authored ShimStacker plans."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from shimstacker.model import Job, Plan, StockBatch

ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
TOP_FIELDS = frozenset({"schema_version", "project", "unit", "max_states", "stock", "jobs"})
STOCK_FIELDS = frozenset({"id", "thickness", "tolerance", "quantity"})
JOB_FIELDS = frozenset({"id", "target_min", "target_max", "max_pieces"})


class PlanError(ValueError):
    """Raised when an authored plan violates the input contract."""


class _DuplicateKeyError(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _object(value: object, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PlanError(f"{path} must be an object")
    return value


def _exact_fields(value: dict[str, Any], expected: frozenset[str], path: str) -> None:
    missing = sorted(expected - value.keys())
    unknown = sorted(value.keys() - expected)
    if missing:
        raise PlanError(f"{path} missing field: {missing[0]}")
    if unknown:
        raise PlanError(f"{path} has unknown field: {unknown[0]}")


def _string(value: object, path: str, *, maximum: int) -> str:
    if not isinstance(value, str):
        raise PlanError(f"{path} must be a string")
    if not value:
        raise PlanError(f"{path} must not be empty")
    if len(value) > maximum:
        raise PlanError(f"{path} must contain at most {maximum} characters")
    return value


def _identifier(value: object, path: str) -> str:
    identifier = _string(value, path, maximum=64)
    if ID_PATTERN.fullmatch(identifier) is None:
        raise PlanError(f"{path} has invalid id")
    return identifier


def _integer(value: object, path: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PlanError(f"{path} must be an integer")
    if not minimum <= value <= maximum:
        raise PlanError(f"{path} must be between {minimum} and {maximum}")
    return value


def _decimal(value: object, path: str, *, positive: bool) -> Decimal:
    if not isinstance(value, str):
        raise PlanError(f"{path} must be a decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise PlanError(f"{path} must be a finite decimal string") from error
    if not number.is_finite():
        raise PlanError(f"{path} must be a finite decimal string")
    if positive and number <= 0:
        raise PlanError(f"{path} must be greater than zero")
    if not positive and number < 0:
        raise PlanError(f"{path} must not be negative")
    return number


def _array(value: object, path: str, *, minimum: int, maximum: int) -> list[Any]:
    if not isinstance(value, list):
        raise PlanError(f"{path} must be an array")
    if not minimum <= len(value) <= maximum:
        raise PlanError(f"{path} must contain between {minimum} and {maximum} entries")
    return value


def _parse_stock(value: object, index: int) -> StockBatch:
    path = f"stock[{index}]"
    item = _object(value, path)
    _exact_fields(item, STOCK_FIELDS, path)
    thickness = _decimal(item["thickness"], f"{path}.thickness", positive=True)
    tolerance = _decimal(item["tolerance"], f"{path}.tolerance", positive=False)
    if tolerance >= thickness:
        raise PlanError(f"{path}.tolerance must be smaller than thickness")
    return StockBatch(
        id=_identifier(item["id"], f"{path}.id"),
        thickness=thickness,
        tolerance=tolerance,
        quantity=_integer(item["quantity"], f"{path}.quantity", minimum=1, maximum=100),
    )


def _parse_job(value: object, index: int) -> Job:
    path = f"jobs[{index}]"
    item = _object(value, path)
    _exact_fields(item, JOB_FIELDS, path)
    target_min = _decimal(item["target_min"], f"{path}.target_min", positive=False)
    target_max = _decimal(item["target_max"], f"{path}.target_max", positive=True)
    if target_max <= target_min:
        raise PlanError(f"{path}.target_max must be greater than target_min")
    return Job(
        id=_identifier(item["id"], f"{path}.id"),
        target_min=target_min,
        target_max=target_max,
        max_pieces=_integer(item["max_pieces"], f"{path}.max_pieces", minimum=1, maximum=8),
    )


def _ensure_unique(values: list[str], kind: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise PlanError(f"duplicate {kind} id: {value}")
        seen.add(value)


def parse_plan_text(text: str) -> Plan:
    """Parse one strict UTF-8 JSON plan from text."""
    try:
        raw = json.loads(text, object_pairs_hook=_unique_object)
    except _DuplicateKeyError as error:
        raise PlanError(f"duplicate object key: {error.args[0]}") from error
    except json.JSONDecodeError as error:
        raise PlanError(f"invalid JSON at line {error.lineno}, column {error.colno}") from error

    root = _object(raw, "root")
    _exact_fields(root, TOP_FIELDS, "root")
    schema_value = root["schema_version"]
    if isinstance(schema_value, bool) or not isinstance(schema_value, int):
        raise PlanError("schema_version must be an integer")
    schema_version = schema_value
    if schema_version != 1:
        raise PlanError("schema_version must equal 1")

    stock_values = _array(root["stock"], "stock", minimum=1, maximum=32)
    job_values = _array(root["jobs"], "jobs", minimum=1, maximum=24)
    stock = [_parse_stock(value, index) for index, value in enumerate(stock_values)]
    jobs = [_parse_job(value, index) for index, value in enumerate(job_values)]
    _ensure_unique([item.id for item in stock], "stock")
    _ensure_unique([item.id for item in jobs], "job")

    return Plan(
        project=_string(root["project"], "project", maximum=120),
        unit=_string(root["unit"], "unit", maximum=16),
        max_states=_integer(root["max_states"], "max_states", minimum=1, maximum=2_000_000),
        stock=tuple(stock),
        jobs=tuple(jobs),
    )

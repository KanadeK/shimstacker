from __future__ import annotations

import json
from pathlib import Path

import pytest

from shimstacker.parse import parse_plan_text
from shimstacker.reports import ARTIFACT_NAMES, ReportError, write_report_bundle
from shimstacker.solver import solve
from tests.helpers import valid_plan_data


def solved(data=None):
    source = valid_plan_data() if data is None else data
    plan = parse_plan_text(json.dumps(source))
    return plan, solve(plan)


def test_report_bundle_is_complete_and_byte_deterministic(tmp_path: Path) -> None:
    plan, result = solved()
    first = tmp_path / "first"
    second = tmp_path / "second"

    write_report_bundle(plan, result, first)
    write_report_bundle(plan, result, second)

    assert {path.name for path in first.iterdir()} == set(ARTIFACT_NAMES)
    for name in ARTIFACT_NAMES:
        assert (first / name).read_bytes() == (second / name).read_bytes()

    payload = json.loads((first / "report.json").read_text(encoding="utf-8"))
    assert payload["status"] == "feasible"
    assert payload["allocations"][0]["stack_min"] == "0.290"
    pick_list = (first / "pick-list.csv").read_text(encoding="utf-8")
    assert "input-bearing,S-010,1" in pick_list
    assert "input-bearing,S-020,1" in pick_list


def test_html_is_script_free_offline_and_escapes_authored_text(tmp_path: Path) -> None:
    data = valid_plan_data()
    data["project"] = "<script>alert('x')</script>"
    plan, result = solved(data)

    write_report_bundle(plan, result, tmp_path / "report")
    html = (tmp_path / "report" / "report.html").read_text(encoding="utf-8")

    assert "<script" not in html.lower()
    assert "https://" not in html.lower()
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in html


def test_infeasible_bundle_carries_machine_readable_evidence(tmp_path: Path) -> None:
    data = valid_plan_data()
    data["stock"] = [{"id": "only", "thickness": "0.10", "tolerance": "0", "quantity": 1}]
    plan, result = solved(data)

    write_report_bundle(plan, result, tmp_path / "report")

    payload = json.loads((tmp_path / "report" / "report.json").read_text(encoding="utf-8"))
    assert payload["status"] == "infeasible"
    assert payload["findings"][0]["code"] == "SHS101"
    assert "SHS101" in (tmp_path / "report" / "bench-sheet.md").read_text(encoding="utf-8")
    assert "SHS101" in (tmp_path / "report" / "report.html").read_text(encoding="utf-8")


def test_existing_output_is_never_overwritten(tmp_path: Path) -> None:
    plan, result = solved()
    output = tmp_path / "report"
    output.mkdir()
    marker = output / "owner.txt"
    marker.write_text("keep", encoding="utf-8")

    with pytest.raises(ReportError, match="already exists"):
        write_report_bundle(plan, result, output)

    assert marker.read_text(encoding="utf-8") == "keep"

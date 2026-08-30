from __future__ import annotations

import json
from pathlib import Path

from shimstacker.cli import main
from shimstacker.reports import ARTIFACT_NAMES
from tests.helpers import valid_plan_data


def write_plan(path: Path, data=None) -> None:
    source = valid_plan_data() if data is None else data
    path.write_text(json.dumps(source), encoding="utf-8")


def test_validate_checks_input_without_creating_output(tmp_path: Path, capsys) -> None:
    source = tmp_path / "plan.json"
    write_plan(source)

    code = main(["validate", str(source)])

    assert code == 0
    assert "valid" in capsys.readouterr().out.lower()
    assert list(tmp_path.iterdir()) == [source]


def test_plan_writes_bundle_and_maps_feasible_exit_code(tmp_path: Path, capsys) -> None:
    source = tmp_path / "plan.json"
    output = tmp_path / "report"
    write_plan(source)

    code = main(["plan", str(source), "--output", str(output)])

    assert code == 0
    assert "FEASIBLE" in capsys.readouterr().out
    assert {path.name for path in output.iterdir()} == set(ARTIFACT_NAMES)


def test_plan_maps_infeasible_and_indeterminate_exit_codes(tmp_path: Path) -> None:
    infeasible = valid_plan_data()
    infeasible["stock"] = [{"id": "only", "thickness": "0.10", "tolerance": "0", "quantity": 1}]
    source = tmp_path / "bad.json"
    write_plan(source, infeasible)
    assert main(["plan", str(source), "--output", str(tmp_path / "bad-report")]) == 1

    limited = valid_plan_data()
    limited["max_states"] = 1
    source = tmp_path / "limited.json"
    write_plan(source, limited)
    assert main(["plan", str(source), "--output", str(tmp_path / "limited-report")]) == 3


def test_invalid_input_returns_two_and_writes_nothing(tmp_path: Path, capsys) -> None:
    source = tmp_path / "invalid.json"
    source.write_text("{}", encoding="utf-8")

    code = main(["plan", str(source), "--output", str(tmp_path / "report")])

    assert code == 2
    assert "error:" in capsys.readouterr().err.lower()
    assert not (tmp_path / "report").exists()


def test_demo_and_version_work_without_source_checkout(tmp_path: Path, capsys) -> None:
    assert main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out

    output = tmp_path / "demo"
    assert main(["demo", "--output", str(output)]) == 0
    assert json.loads((output / "report.json").read_text(encoding="utf-8"))["status"] == "feasible"

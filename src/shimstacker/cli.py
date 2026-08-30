"""Command-line interface for ShimStacker."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING

from shimstacker import __version__
from shimstacker.parse import PlanError, parse_plan_text
from shimstacker.reports import ReportError, write_report_bundle
from shimstacker.solver import SolveResult, solve

if TYPE_CHECKING:
    from shimstacker.model import Plan


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shimstacker",
        description="Allocate finite shim stock with worst-case tolerance proof.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate one plan without solving it")
    validate.add_argument("plan", type=Path)
    plan = commands.add_parser("plan", help="solve a plan and write a report bundle")
    plan.add_argument("plan", type=Path)
    plan.add_argument("--output", type=Path, required=True)
    demo = commands.add_parser("demo", help="solve the packaged feasible example")
    demo.add_argument("--output", type=Path, required=True)
    return parser


def _load(path: Path) -> Plan:
    return parse_plan_text(path.read_text(encoding="utf-8"))


def _demo_plan() -> Plan:
    source = files("shimstacker").joinpath("examples/feasible-shop.json")
    return parse_plan_text(source.read_text(encoding="utf-8"))


def _finish(plan: Plan, output: Path) -> tuple[int, SolveResult]:
    result = solve(plan)
    write_report_bundle(plan, result, output)
    code = {"feasible": 0, "infeasible": 1, "indeterminate": 3}[result.status]
    return code, result


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return its documented process code."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--version"]:
        print(f"shimstacker {__version__}")
        return 0

    args = _parser().parse_args(arguments)
    try:
        if args.command == "validate":
            plan = _load(args.plan)
            print(
                f"VALID · {plan.project} · {len(plan.stock)} stock batches · {len(plan.jobs)} jobs"
            )
            return 0
        plan = _demo_plan() if args.command == "demo" else _load(args.plan)
        code, result = _finish(plan, args.output)
    except (OSError, PlanError, ReportError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(
        f"{result.status.upper()} · {len(result.allocations)}/{len(plan.jobs)} jobs allocated · "
        f"{result.states_explored} states · {args.output}"
    )
    return code

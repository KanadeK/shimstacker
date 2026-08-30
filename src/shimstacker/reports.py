"""Deterministic report rendering and atomic bundle publication."""

from __future__ import annotations

import csv
import html
import io
import json
import shutil
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shimstacker.model import Plan
    from shimstacker.solver import Allocation, SolveResult

ARTIFACT_NAMES = ("report.json", "pick-list.csv", "bench-sheet.md", "report.html")


class ReportError(RuntimeError):
    """Raised when a report bundle cannot be published safely."""


def _number(value: Decimal) -> str:
    return format(value, "f")


def _allocation_record(item: Allocation) -> dict[str, object]:
    return {
        "job_id": item.job_id,
        "parts": [{"stock_id": stock_id, "quantity": count} for stock_id, count in item.parts],
        "piece_count": item.piece_count,
        "nominal": _number(item.nominal),
        "stack_min": _number(item.stack_min),
        "stack_max": _number(item.stack_max),
        "target_min": _number(item.target_min),
        "target_max": _number(item.target_max),
        "deviation": _number(item.deviation),
    }


def _payload(plan: Plan, result: SolveResult) -> dict[str, object]:
    allocated = dict.fromkeys((item.id for item in plan.stock), 0)
    for allocation in result.allocations:
        for stock_id, count in allocation.parts:
            allocated[stock_id] += count
    return {
        "schema_version": 1,
        "project": plan.project,
        "unit": plan.unit,
        "status": result.status,
        "states_explored": result.states_explored,
        "stock": [
            {
                "id": item.id,
                "thickness": _number(item.thickness),
                "tolerance": _number(item.tolerance),
                "quantity": item.quantity,
                "allocated": allocated[item.id],
                "remaining": item.quantity - allocated[item.id],
            }
            for item in sorted(plan.stock, key=lambda value: value.id)
        ],
        "allocations": [_allocation_record(item) for item in result.allocations],
        "findings": [
            {"code": item.code, "message": item.message, "subjects": list(item.subjects)}
            for item in result.findings
        ],
    }


def _json_report(plan: Plan, result: SolveResult) -> str:
    return json.dumps(_payload(plan, result), indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _csv_report(plan: Plan, result: SolveResult) -> str:
    batches = {item.id: item for item in plan.stock}
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        [
            "job_id",
            "stock_id",
            "quantity",
            "thickness",
            "tolerance",
            "stack_min",
            "nominal",
            "stack_max",
            "target_min",
            "target_max",
            "unit",
        ]
    )
    for allocation in result.allocations:
        for stock_id, count in allocation.parts:
            batch = batches[stock_id]
            writer.writerow(
                [
                    allocation.job_id,
                    stock_id,
                    count,
                    _number(batch.thickness),
                    _number(batch.tolerance),
                    _number(allocation.stack_min),
                    _number(allocation.nominal),
                    _number(allocation.stack_max),
                    _number(allocation.target_min),
                    _number(allocation.target_max),
                    plan.unit,
                ]
            )
    return stream.getvalue()


def _markdown_text(value: str) -> str:
    return html.escape(value, quote=False).replace("|", "\\|").replace("\n", " ")


def _markdown_report(plan: Plan, result: SolveResult) -> str:
    lines = [
        f"# {_markdown_text(plan.project)} — shim bench sheet",
        "",
        f"**Outcome:** `{result.status.upper()}`  ",
        f"**Search states:** {result.states_explored}  ",
        f"**Unit:** {_markdown_text(plan.unit)}",
        "",
    ]
    if result.allocations:
        lines.extend(
            [
                "## Pick plan",
                "",
                "| Job | Pick | Proven stack | Target |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in result.allocations:
            picks = ", ".join(
                f"{count} x {_markdown_text(stock_id)}" for stock_id, count in item.parts
            )
            lines.append(
                f"| `{item.job_id}` | {picks} | {_number(item.stack_min)}-{_number(item.stack_max)} "
                f"(nominal {_number(item.nominal)}) | {_number(item.target_min)}-{_number(item.target_max)} |"
            )
        lines.append("")
    if result.findings:
        lines.extend(["## Findings", ""])
        lines.extend(
            f"- **{finding.code}** - {_markdown_text(finding.message)}"
            for finding in result.findings
        )
        lines.append("")
    lines.extend(
        [
            "## Required bench verification",
            "",
            "This allocation proves only the arithmetic declared in the input. Confirm shim identity, material suitability, actual assembled clearance, and the equipment manufacturer's procedure before operation.",
            "",
        ]
    )
    return "\n".join(lines)


def _bar(item: Allocation) -> str:
    width = Decimal(500)
    scale = max(item.target_max, item.stack_max)
    target_x = int(item.target_min * width / scale)
    target_width = max(1, int((item.target_max - item.target_min) * width / scale))
    stack_x = int(item.stack_min * width / scale)
    stack_width = max(1, int((item.stack_max - item.stack_min) * width / scale))
    return (
        '<svg viewBox="0 0 500 30" role="img" aria-label="Target and proven thickness bands">'
        f'<rect class="target" x="{target_x}" y="5" width="{target_width}" height="20" rx="4"/>'
        f'<rect class="stack" x="{stack_x}" y="10" width="{stack_width}" height="10" rx="3"/>'
        "</svg>"
    )


def _html_report(plan: Plan, result: SolveResult) -> str:
    cards: list[str] = []
    for item in result.allocations:
        picks = " · ".join(
            f"<strong>{count}x</strong> {html.escape(stock_id)}" for stock_id, count in item.parts
        )
        cards.append(
            '<article class="card">'
            f'<h2>{html.escape(item.job_id)}</h2><p class="picks">{picks}</p>'
            f"{_bar(item)}"
            f"<p><b>Proven:</b> {_number(item.stack_min)}-{_number(item.stack_max)} {html.escape(plan.unit)} "
            f"· <b>Target:</b> {_number(item.target_min)}-{_number(item.target_max)} {html.escape(plan.unit)}</p>"
            "</article>"
        )
    cards.extend(
        (
            '<article class="card finding">'
            f"<h2>{html.escape(finding.code)}</h2><p>{html.escape(finding.message)}</p>"
            "</article>"
        )
        for finding in result.findings
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(plan.project)} · ShimStacker</title>
<style>
:root{{--ink:#182018;--paper:#f3f0e5;--panel:#fffdf6;--accent:#e06b3c;--green:#28785b;--muted:#667064}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:980px;margin:auto;padding:48px 22px}}header{{border-bottom:3px solid var(--ink);margin-bottom:28px}}
.eyebrow{{font:700 12px/1.2 ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
h1{{font-size:clamp(2.3rem,7vw,5.5rem);line-height:.92;margin:.2em 0}}.status{{display:inline-block;padding:7px 11px;background:var(--ink);color:white;font-weight:800}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}}.card{{background:var(--panel);border:1px solid #c8c7bb;border-radius:14px;padding:20px;box-shadow:5px 5px 0 #d5d1c2}}
.card h2{{margin:0 0 8px;font:800 1.15rem ui-monospace,monospace}}.picks{{font-size:1.08rem}}svg{{display:block;width:100%;margin:18px 0}}.target{{fill:#f1c6af}}.stack{{fill:var(--green)}}
.finding{{border-color:var(--accent)}}footer{{margin-top:30px;padding-top:16px;border-top:1px solid #aaa;color:var(--muted)}}
</style></head><body><main><header><p class="eyebrow">Exact finite-stock tolerance evidence</p>
<h1>{html.escape(plan.project)}</h1><p><span class="status">{result.status.upper()}</span> · {result.states_explored} search states · {html.escape(plan.unit)}</p></header>
<section class="grid">{"".join(cards)}</section><footer>This report proves only the declared arithmetic. Verify the physical assembly and manufacturer procedure before operation.</footer>
</main></body></html>
"""


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def write_report_bundle(plan: Plan, result: SolveResult, output: Path) -> None:
    """Write all report artifacts, then publish the new directory in one rename."""
    output = output.resolve()
    if output.exists():
        raise ReportError(f"output already exists: {output}")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".shimstacker-", dir=output.parent))
    except OSError as error:
        raise ReportError(f"cannot prepare report output: {error}") from error

    try:
        _write_text(staging / "report.json", _json_report(plan, result))
        _write_text(staging / "pick-list.csv", _csv_report(plan, result))
        _write_text(staging / "bench-sheet.md", _markdown_report(plan, result))
        _write_text(staging / "report.html", _html_report(plan, result))
        if output.exists():
            raise ReportError(f"output already exists: {output}")
        staging.replace(output)
    except OSError as error:
        raise ReportError(f"cannot publish report bundle: {error}") from error
    finally:
        if staging.exists():
            shutil.rmtree(staging)

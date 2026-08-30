"""Exact bounded allocation of finite shim stock."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from shimstacker.model import Job, Plan, StockBatch

ZERO = Decimal(0)
Status = Literal["feasible", "infeasible", "indeterminate"]
AllocationSignature = tuple[tuple[str, tuple[tuple[str, int], ...]], ...]
ObjectiveKey = tuple[int, Decimal, AllocationSignature]


@dataclass(frozen=True, slots=True)
class Finding:
    """Machine-readable evidence about a solver outcome."""

    code: str
    message: str
    subjects: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Allocation:
    """One proven stack allocated to one job."""

    job_id: str
    parts: tuple[tuple[str, int], ...]
    piece_count: int
    nominal: Decimal
    stack_min: Decimal
    stack_max: Decimal
    target_min: Decimal
    target_max: Decimal
    deviation: Decimal


@dataclass(frozen=True, slots=True)
class SolveResult:
    """Complete solver result."""

    status: Status
    allocations: tuple[Allocation, ...]
    findings: tuple[Finding, ...]
    states_explored: int


@dataclass(frozen=True, slots=True)
class _Combination:
    parts: tuple[tuple[str, int], ...]
    piece_count: int
    nominal: Decimal
    stack_min: Decimal
    stack_max: Decimal
    deviation: Decimal

    @property
    def counts(self) -> dict[str, int]:
        return dict(self.parts)


class _LimitReachedError(RuntimeError):
    pass


@dataclass(slots=True)
class _Budget:
    limit: int
    used: int = 0

    def spend(self) -> None:
        if self.used >= self.limit:
            raise _LimitReachedError
        self.used += 1


@dataclass(frozen=True, slots=True)
class _StackState:
    index: int = 0
    pieces: int = 0
    nominal: Decimal = ZERO
    stack_min: Decimal = ZERO
    stack_max: Decimal = ZERO
    parts: tuple[tuple[str, int], ...] = ()


def _combination_key(item: _Combination) -> tuple[int, Decimal, tuple[tuple[str, int], ...]]:
    return item.piece_count, item.deviation, item.parts


def _enumerate_job(
    job: Job,
    stock: tuple[StockBatch, ...],
    budget: _Budget,
) -> tuple[_Combination, ...]:
    found: list[_Combination] = []

    def visit(state: _StackState) -> None:
        budget.spend()
        if state.stack_min > job.target_max:
            return
        if state.index == len(stock):
            if (
                state.pieces
                and job.target_min <= state.stack_min
                and state.stack_max <= job.target_max
            ):
                found.append(
                    _Combination(
                        parts=state.parts,
                        piece_count=state.pieces,
                        nominal=state.nominal,
                        stack_min=state.stack_min,
                        stack_max=state.stack_max,
                        deviation=abs(state.nominal - job.midpoint),
                    )
                )
            return

        batch = stock[state.index]
        available = min(batch.quantity, job.max_pieces - state.pieces)
        for count in range(available + 1):
            next_parts = state.parts if count == 0 else (*state.parts, (batch.id, count))
            visit(
                _StackState(
                    index=state.index + 1,
                    pieces=state.pieces + count,
                    nominal=state.nominal + batch.thickness * count,
                    stack_min=state.stack_min + batch.minimum * count,
                    stack_max=state.stack_max + batch.maximum * count,
                    parts=next_parts,
                )
            )

    visit(_StackState())
    found.sort(key=_combination_key)
    return tuple(found)


def _allocation(job: Job, combination: _Combination) -> Allocation:
    return Allocation(
        job_id=job.id,
        parts=combination.parts,
        piece_count=combination.piece_count,
        nominal=combination.nominal,
        stack_min=combination.stack_min,
        stack_max=combination.stack_max,
        target_min=job.target_min,
        target_max=job.target_max,
        deviation=combination.deviation,
    )


def _allocation_signature(
    selected: dict[str, _Combination],
) -> AllocationSignature:
    return tuple((job_id, selected[job_id].parts) for job_id in sorted(selected))


def _cannot_improve(best_key: ObjectiveKey | None, piece_count: int, deviation: Decimal) -> bool:
    if best_key is None:
        return False
    return piece_count > best_key[0] or (piece_count == best_key[0] and deviation > best_key[1])


def _find_best_allocation(
    jobs: tuple[Job, ...],
    candidates: dict[str, tuple[_Combination, ...]],
    quantities: dict[str, int],
    budget: _Budget,
) -> dict[str, _Combination] | None:
    order = sorted(jobs, key=lambda item: (len(candidates[item.id]), item.id))
    used = dict.fromkeys(quantities, 0)
    selected: dict[str, _Combination] = {}
    best: dict[str, _Combination] | None = None
    best_key: ObjectiveKey | None = None

    def search(index: int, piece_count: int, deviation: Decimal) -> None:
        nonlocal best, best_key
        budget.spend()
        if _cannot_improve(best_key, piece_count, deviation):
            return
        if index == len(order):
            key = piece_count, deviation, _allocation_signature(selected)
            if best_key is None or key < best_key:
                best_key = key
                best = dict(selected)
            return

        job = order[index]
        for option in candidates[job.id]:
            counts = option.counts
            if any(
                used[stock_id] + count > quantities[stock_id] for stock_id, count in counts.items()
            ):
                continue
            for stock_id, count in counts.items():
                used[stock_id] += count
            selected[job.id] = option
            search(index + 1, piece_count + option.piece_count, deviation + option.deviation)
            del selected[job.id]
            for stock_id, count in counts.items():
                used[stock_id] -= count

    search(0, 0, ZERO)
    return best


def solve(plan: Plan) -> SolveResult:
    """Find the globally best guaranteed allocation within the authored state limit."""
    budget = _Budget(plan.max_states)
    stock = tuple(sorted(plan.stock, key=lambda item: item.id))
    jobs_by_id = {job.id: job for job in plan.jobs}

    try:
        candidates: dict[str, tuple[_Combination, ...]] = {}
        for job in sorted(plan.jobs, key=lambda item: item.id):
            options = _enumerate_job(job, stock, budget)
            if not options:
                finding = Finding(
                    code="SHS101",
                    message=f"Job {job.id} has no guaranteed stack within its target band.",
                    subjects=(job.id,),
                )
                return SolveResult("infeasible", (), (finding,), budget.used)
            candidates[job.id] = options

        quantities = {batch.id: batch.quantity for batch in stock}
        best = _find_best_allocation(plan.jobs, candidates, quantities, budget)
    except _LimitReachedError:
        finding = Finding(
            code="SHS199",
            message=f"The search reached max_states={plan.max_states} before proving an outcome.",
            subjects=(),
        )
        return SolveResult("indeterminate", (), (finding,), budget.used)

    if best is None:
        subjects = tuple(sorted(jobs_by_id))
        finding = Finding(
            code="SHS102",
            message="Every job is individually possible, but shared stock cannot satisfy all jobs.",
            subjects=subjects,
        )
        return SolveResult("infeasible", (), (finding,), budget.used)

    allocations = tuple(_allocation(jobs_by_id[job_id], best[job_id]) for job_id in sorted(best))
    return SolveResult("feasible", allocations, (), budget.used)

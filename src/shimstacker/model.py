"""Immutable domain values for ShimStacker."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class StockBatch:
    """One interchangeable batch of shims."""

    id: str
    thickness: Decimal
    tolerance: Decimal
    quantity: int

    @property
    def minimum(self) -> Decimal:
        """Return the stated minimum thickness of one piece."""
        return self.thickness - self.tolerance

    @property
    def maximum(self) -> Decimal:
        """Return the stated maximum thickness of one piece."""
        return self.thickness + self.tolerance


@dataclass(frozen=True, slots=True)
class Job:
    """One assembly gap that needs a shim stack."""

    id: str
    target_min: Decimal
    target_max: Decimal
    max_pieces: int

    @property
    def midpoint(self) -> Decimal:
        """Return the midpoint of the accepted target band."""
        return (self.target_min + self.target_max) / 2


@dataclass(frozen=True, slots=True)
class Plan:
    """Validated source-of-truth shim allocation plan."""

    project: str
    unit: str
    max_states: int
    stock: tuple[StockBatch, ...]
    jobs: tuple[Job, ...]

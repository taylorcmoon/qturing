"""ca.py — cellular automaton simulation engine.

Provides ``run()`` and ``run_2d()`` for batch simulation and ``trace_1d()`` /
``trace_2d()`` for lazy, generation-by-generation iteration.

Design notes
------------
* No mutable state: every step returns a new tuple; the lookup table is built
  once per run and never modified.
* ``_build_lookup()`` generalises to any k-color, r-radius rule, not just the
  elementary (k=2, r=1) case.
* ``step_1d()`` and ``step_2d()`` are pure functions — they can be tested in
  isolation and composed into larger pipelines.
* Boundary handling is centralised in ``_pad_1d()`` and the neighbour counter
  so neither step function needs to know about boundary conditions.
"""

from __future__ import annotations

import time
from typing import Iterator

from .types import (
    CABoundary,
    CAConfig,
    CAGeneration,
    CARule,
    CARunResult,
    CA2DConfig,
    CA2DGeneration,
    CA2DRunResult,
)

# ---------------------------------------------------------------------------
# 1D — lookup table
# ---------------------------------------------------------------------------


def _build_lookup(rule: CARule) -> dict[tuple[int, ...], int]:
    """Precompute neighbourhood -> output cell value for any Wolfram rule.

    For elementary (k=2, r=1) this produces 8 entries in ~1 µs.
    For (k=3, r=1) it produces 27 entries; (k=2, r=2) produces 32 entries.

    The encoding follows Wolfram's convention: neighbourhood patterns are
    enumerated in descending lex order and the rule number is decoded
    digit-by-digit in base k.
    """
    k = rule.num_colors
    n = rule.neighborhood
    total = k ** n
    lookup: dict[tuple[int, ...], int] = {}

    for i in range(total):
        # Decode neighbourhood pattern (big-endian base-k representation of i)
        pattern = tuple((i // (k ** j)) % k for j in range(n - 1, -1, -1))
        # Decode output value from the rule number
        output = (rule.rule_number // (k ** i)) % k
        lookup[pattern] = output

    return lookup


# ---------------------------------------------------------------------------
# 1D — boundary padding
# ---------------------------------------------------------------------------


def _pad_1d(
    cells: tuple[int, ...],
    radius: int,
    boundary: CABoundary,
) -> tuple[int, ...]:
    """Return cells extended on both sides by ``radius`` ghost cells."""
    if boundary.mode == "periodic":
        left = cells[-radius:]
        right = cells[:radius]
    elif boundary.mode == "fixed":
        left = (boundary.pad_value,) * radius
        right = (boundary.pad_value,) * radius
    else:  # "zero"
        left = (0,) * radius
        right = (0,) * radius
    return left + cells + right


# ---------------------------------------------------------------------------
# 1D — core step
# ---------------------------------------------------------------------------


def step_1d(
    cells: tuple[int, ...],
    lookup: dict[tuple[int, ...], int],
    rule: CARule,
    boundary: CABoundary,
) -> tuple[int, ...]:
    """Advance one generation. Returns a new tuple of the same length.

    Parameters
    ----------
    cells:
        Current generation as an immutable tuple of cell values.
    lookup:
        Precomputed neighbourhood -> output map from ``_build_lookup()``.
    rule:
        The CARule (used for radius and validation, not re-computed here).
    boundary:
        How to handle cells at the edges.
    """
    r = rule.radius
    n = rule.neighborhood
    padded = _pad_1d(cells, r, boundary)
    return tuple(lookup[padded[i : i + n]] for i in range(len(cells)))


# ---------------------------------------------------------------------------
# 1D — batch and lazy runners
# ---------------------------------------------------------------------------


def run(config: CAConfig) -> CARunResult:
    """Simulate a 1D CA and return all generations in one result object.

    Builds the lookup table once, then iterates.  For rule 30 on a width-200
    tape, 10 000 generations run in well under a second on a modern machine.

    Example
    -------
    >>> rule30 = CARule(rule_number=30)
    >>> seed = (0,) * 99 + (1,) + (0,) * 100  # single live cell at centre
    >>> config = CAConfig(rule=rule30, width=200, seed=seed, generations=100)
    >>> result = run(config)
    >>> result.num_generations
    101
    >>> len(result.grid[0])
    200
    """
    t0 = time.perf_counter()
    lookup = _build_lookup(config.rule)

    current = config.seed
    generations: list[CAGeneration] = [CAGeneration(index=0, cells=current)]

    for gen in range(1, config.generations + 1):
        current = step_1d(current, lookup, config.rule, config.boundary)
        generations.append(CAGeneration(index=gen, cells=current))

    elapsed_ms = (time.perf_counter() - t0) * 1_000
    return CARunResult(config=config, generations=generations, elapsed_ms=elapsed_ms)


def trace_1d(config: CAConfig) -> Iterator[CAGeneration]:
    """Yield each generation lazily — useful for streaming to a renderer.

    The lookup table is built on first call; subsequent yields are O(width).

    Example
    -------
    >>> for gen in trace_1d(config):
    ...     render(gen)   # draw one row at a time
    """
    lookup = _build_lookup(config.rule)
    current = config.seed
    yield CAGeneration(index=0, cells=current)

    for gen in range(1, config.generations + 1):
        current = step_1d(current, lookup, config.rule, config.boundary)
        yield CAGeneration(index=gen, cells=current)


# ---------------------------------------------------------------------------
# 2D — neighbour counter
# ---------------------------------------------------------------------------


def _moore_neighbours(
    grid: tuple[tuple[int, ...], ...],
    row: int,
    col: int,
    rows: int,
    cols: int,
    boundary: CABoundary,
) -> int:
    """Count live (non-zero) Moore neighbours for cell (row, col)."""
    total = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            r, c = row + dr, col + dc
            if boundary.mode == "periodic":
                total += grid[r % rows][c % cols]
            elif 0 <= r < rows and 0 <= c < cols:
                total += grid[r][c]
            elif boundary.mode == "fixed":
                total += boundary.pad_value
            # else: "zero" boundary — out-of-bounds cells count as 0
    return total


# ---------------------------------------------------------------------------
# 2D — core step
# ---------------------------------------------------------------------------


def step_2d(
    grid: tuple[tuple[int, ...], ...],
    config: CA2DConfig,
) -> tuple[tuple[int, ...], ...]:
    """Advance one generation of a 2D outer-totalistic CA.

    Returns a new fully-immutable grid of the same shape.
    """
    rows = config.rows
    cols = config.cols
    new_rows: list[tuple[int, ...]] = []

    for r in range(rows):
        new_row: list[int] = []
        for c in range(cols):
            n = _moore_neighbours(grid, r, c, rows, cols, config.boundary)
            alive = grid[r][c]
            if alive:
                new_row.append(1 if n in config.survival else 0)
            else:
                new_row.append(1 if n in config.birth else 0)
        new_rows.append(tuple(new_row))

    return tuple(new_rows)


# ---------------------------------------------------------------------------
# 2D — batch and lazy runners
# ---------------------------------------------------------------------------


def run_2d(config: CA2DConfig) -> CA2DRunResult:
    """Simulate a 2D CA and return all generations in one result object.

    Example
    -------
    >>> glider = (
    ...     (0,1,0),
    ...     (0,0,1),
    ...     (1,1,1),
    ... )
    >>> cfg = CA2DConfig.game_of_life(
    ...     grid=glider, generations=20
    ... )
    >>> result = run_2d(cfg)
    >>> result.population_series()[:5]
    [5, 5, 5, 5, 5]
    """
    t0 = time.perf_counter()
    current = config.grid
    generations: list[CA2DGeneration] = [CA2DGeneration(index=0, grid=current)]

    for gen in range(1, config.generations + 1):
        current = step_2d(current, config)
        generations.append(CA2DGeneration(index=gen, grid=current))

    elapsed_ms = (time.perf_counter() - t0) * 1_000
    return CA2DRunResult(config=config, generations=generations, elapsed_ms=elapsed_ms)


def trace_2d(config: CA2DConfig) -> Iterator[CA2DGeneration]:
    """Yield each 2D generation lazily.

    Prefer this over ``run_2d()`` when rendering frame-by-frame or when
    the full history would be too large to hold in memory.
    """
    current = config.grid
    yield CA2DGeneration(index=0, grid=current)

    for gen in range(1, config.generations + 1):
        current = step_2d(current, config)
        yield CA2DGeneration(index=gen, grid=current)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def single_cell_seed(width: int, rule: CARule | None = None) -> tuple[int, ...]:
    """Return a seed tuple with a single live cell at the centre.

    This is the canonical starting point for visualising elementary CA rules
    (rule 30, rule 110, etc.).
    """
    mid = width // 2
    return (0,) * mid + (1,) + (0,) * (width - mid - 1)


def random_seed(
    width: int,
    density: float = 0.5,
    seed: int | None = None,
) -> tuple[int, ...]:
    """Return a random binary seed with approximately ``density`` live cells.

    Parameters
    ----------
    width:
        Number of cells.
    density:
        Fraction of cells that start alive (0.0–1.0).
    seed:
        Optional random seed for reproducibility.
    """
    import random
    rng = random.Random(seed)
    return tuple(1 if rng.random() < density else 0 for _ in range(width))

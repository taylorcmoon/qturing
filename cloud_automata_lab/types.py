"""types.py — shared dataclasses and type aliases for Cloud Automata Lab.

Defines the full type hierarchy used across the package:
- Turing machine specs (``TuringMachineSpec``, ``Transition``, ``TapeSnapshot``)
- Quantum Turing machine specs (``QTransition``, ``QTuringMachineSpec``, ``Wavefunction``)
- Cloud client types (``CloudSettings``, ``CloudRequest``, ``CloudResponse``)
- Cellular automaton configs and results (1D and 2D)
- Wolfram expression and export types

Author:  Taylor Moon <taylorcmoon>
License: Proprietary — All Rights Reserved
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


# ---------------------------------------------------------------------------
# Turing machine core
# ---------------------------------------------------------------------------

SimResult = Literal["ACCEPT", "REJECT", "TIMEOUT"]
Move = Literal["L", "R", "S"]


@dataclass(frozen=True)
class Transition:
    id: str
    state: str
    read: str
    write: str
    move: Move
    next_state: str


TransitionTable = dict[tuple[str, str], Transition]


@dataclass
class TuringMachineSpec:
    name: str
    alphabet: list[str]
    blank_symbol: str
    start_state: str
    accept_state: str
    reject_state: str
    input_tape: str
    transitions: list[Transition]


@dataclass(frozen=True)
class TapeSnapshot:
    cells: tuple[str, ...]
    head: int
    offset: int = 0

    def logical_head(self) -> int:
        return self.head - self.offset

    def to_str(self, blank: str = "_") -> str:
        return "".join(self.cells).strip(blank)


@dataclass(frozen=True)
class SimulationStep:
    step: int
    state: str
    snapshot: TapeSnapshot


@dataclass
class SimulationOutcome:
    result: SimResult
    final_tape: str
    steps: int
    history: list[SimulationStep]


# ---------------------------------------------------------------------------
# Quantum Turing machine
# ---------------------------------------------------------------------------

# A basis configuration: (internal_state, tape_cells, head_position)
Configuration = tuple[str, tuple[str, ...], int]

# The wavefunction: a superposition of configurations with complex amplitudes.
# |ψ⟩ = Σ αᵢ |qᵢ, tᵢ, hᵢ⟩   where Σ|αᵢ|² = 1 (after normalisation)
Wavefunction = dict[Configuration, complex]


@dataclass(frozen=True)
class QTransition:
    """One branch of a quantum transition.

    A single (state, read) pair may have multiple QTransitions — each with its
    own complex amplitude.  The set of amplitudes for a given (state, symbol)
    must be unitary (squared magnitudes sum to 1) to preserve the norm.
    """
    id: str
    state: str
    read: str
    amplitude: complex
    write: str
    move: Move
    next_state: str


@dataclass
class QTuringMachineSpec:
    """Quantum Turing machine — like TuringMachineSpec but with QTransitions."""
    name: str
    alphabet: list[str]
    blank_symbol: str
    start_state: str
    accept_state: str
    reject_state: str
    input_tape: str
    transitions: list[QTransition]


@dataclass(frozen=True)
class QSimulationStep:
    """A snapshot of the wavefunction at one simulation step."""
    step: int
    wavefunction: Wavefunction

    def probabilities(self) -> dict[Configuration, float]:
        return {cfg: abs(a) ** 2 for cfg, a in self.wavefunction.items()}


@dataclass
class QMeasurementOutcome:
    """One possible classical outcome after measuring the wavefunction."""
    result: SimResult
    final_tape: str
    probability: float


@dataclass
class QSimulationOutcome:
    """Full result of a quantum Turing machine run."""
    result: SimResult          # most-probable outcome
    final_tape: str
    steps: int
    history: list[QSimulationStep]
    measurement_outcomes: list[QMeasurementOutcome]

    def dominant_probability(self) -> float:
        return self.measurement_outcomes[0].probability if self.measurement_outcomes else 0.0


# ---------------------------------------------------------------------------
# Cloud
# ---------------------------------------------------------------------------

@dataclass
class CloudSettings:
    endpoint_url: str = ""
    api_key: str = ""
    mode: ExecutionMode = "mock"
    wolfram_id: str = ""
    wolfram_password: str = ""


@dataclass
class CloudRequest:
    code: str
    parameters: dict[str, Any] | None = None
    timeout: float = 30.0


@dataclass
class CloudResponse:
    ok: bool
    result: str
    executed_at: str
    error: str | None = None
    raw: object = None


# ---------------------------------------------------------------------------
# Workspace / presets
# ---------------------------------------------------------------------------

@dataclass
class WorkspaceCommand:
    id: str
    title: str
    description: str
    code: str


@dataclass
class ModelingPreset:
    id: str
    title: str
    category: str
    description: str
    wolfram_code: str


# ---------------------------------------------------------------------------
# Cellular automaton — 1D
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CARule:
    rule_number: int
    neighborhood: int = 3
    num_colors: int = 2

    def __post_init__(self) -> None:
        max_rule = self.num_colors ** (self.num_colors ** self.neighborhood)
        if not (0 <= self.rule_number < max_rule):
            raise ValueError(
                f"rule_number {self.rule_number} out of range 0-{max_rule - 1}"
            )

    @property
    def radius(self) -> int:
        return self.neighborhood // 2

    def wolfram_spec(self) -> tuple[int, int, int]:
        return (self.rule_number, self.num_colors, self.radius)


@dataclass(frozen=True)
class CABoundary:
    mode: Literal["periodic", "fixed", "zero"] = "zero"
    pad_value: int = 0


@dataclass(frozen=True)
class CAConfig:
    rule: CARule
    width: int
    seed: tuple[int, ...]
    boundary: CABoundary = field(default_factory=CABoundary)
    generations: int = 64

    def __post_init__(self) -> None:
        if len(self.seed) != self.width:
            raise ValueError(f"seed length {len(self.seed)} must equal width {self.width}")
        bad = [c for c in self.seed if not (0 <= c < self.rule.num_colors)]
        if bad:
            raise ValueError(f"seed contains values outside [0, {self.rule.num_colors}): {bad}")


@dataclass(frozen=True)
class CAGeneration:
    index: int
    cells: tuple[int, ...]


@dataclass
class CARunResult:
    config: CAConfig
    generations: list[CAGeneration]
    elapsed_ms: float

    @property
    def grid(self) -> list[tuple[int, ...]]:
        return [g.cells for g in self.generations]

    @property
    def num_generations(self) -> int:
        return len(self.generations)


# ---------------------------------------------------------------------------
# Cellular automaton — 2D
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CA2DConfig:
    rule_name: str
    birth: frozenset[int]
    survival: frozenset[int]
    grid: tuple[tuple[int, ...], ...]
    boundary: CABoundary = field(default_factory=CABoundary)
    generations: int = 64

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    @classmethod
    def game_of_life(cls, grid: tuple[tuple[int, ...], ...], generations: int = 64, boundary: CABoundary | None = None) -> CA2DConfig:
        return cls(rule_name="game_of_life", birth=frozenset({3}), survival=frozenset({2, 3}), grid=grid, boundary=boundary or CABoundary(), generations=generations)


@dataclass(frozen=True)
class CA2DGeneration:
    index: int
    grid: tuple[tuple[int, ...], ...]

    def population(self) -> int:
        return sum(c for row in self.grid for c in row)


@dataclass
class CA2DRunResult:
    config: CA2DConfig
    generations: list[CA2DGeneration]
    elapsed_ms: float

    @property
    def num_generations(self) -> int:
        return len(self.generations)

    def population_series(self) -> list[int]:
        return [g.population() for g in self.generations]


# ---------------------------------------------------------------------------
# Wolfram / export
# ---------------------------------------------------------------------------

ExecutionMode = Literal["mock", "live"]
PresetCategory = Literal["automata", "systems", "dynamics"]
ExportFormat = Literal["png", "gif", "json", "csv"]


@dataclass(frozen=True)
class WolframExpression:
    head: Literal["TuringMachine", "CellularAutomaton", "Graph", "Custom"]
    code: str
    expected_output: Literal["image", "list", "graph", "string"] = "string"

    def to_request(self, parameters: dict[str, Any] | None = None, timeout: float = 30.0) -> CloudRequest:
        return CloudRequest(code=self.code, parameters=parameters, timeout=timeout)


@dataclass(frozen=True)
class ExportOptions:
    format: ExportFormat
    width_px: int = 800
    cell_px: int = 4
    fps: int = 10
    colormap: dict[int, tuple[int, int, int]] | None = None
    include_metadata: bool = True


@dataclass
class ExportResult:
    path: Path
    format: ExportFormat
    size_bytes: int
    width_px: int
    height_px: int
    elapsed_ms: float

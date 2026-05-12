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
# Cloud
# ---------------------------------------------------------------------------

@dataclass
class CloudSettings:
    endpoint_url: str = ""
    api_key: str = ""
    mode: ExecutionMode = "mock"


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

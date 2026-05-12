from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Literal

from .types import TuringMachineSpec

SimResult = Literal["ACCEPT", "REJECT", "TIMEOUT"]


@dataclass
class SimulationStep:
    step: int
    state: str
    head: int
    tape: str


@dataclass
class SimulationOutcome:
    result: SimResult
    final_tape: str
    steps: int
    history: list[SimulationStep]


def simulate(
    machine: TuringMachineSpec,
    tape: str | None = None,
    max_steps: int = 10_000,
    record_history: bool = False,
) -> SimulationOutcome:
    """Run the Turing machine locally. Mirrors the semantics of the exported runners."""
    blank = machine.blank_symbol
    initial = tape if tape is not None else machine.input_tape
    cells: list[str] = list(initial) if initial else [blank]
    head = 0
    state = machine.start_state
    table = {(t.state, t.read): t for t in machine.transitions}
    history: list[SimulationStep] = []

    for steps in range(max_steps):
        if record_history:
            history.append(SimulationStep(steps, state, head, "".join(cells)))

        if state == machine.accept_state:
            return SimulationOutcome("ACCEPT", _trim(cells, blank), steps, history)
        if state == machine.reject_state:
            return SimulationOutcome("REJECT", _trim(cells, blank), steps, history)

        while head < 0:
            cells.insert(0, blank)
            head = 0
        while head >= len(cells):
            cells.append(blank)

        rule = table.get((state, cells[head]))
        if rule is None:
            return SimulationOutcome("REJECT", _trim(cells, blank), steps, history)

        cells[head] = rule.write
        state = rule.next_state
        if rule.move == "R":
            head += 1
        elif rule.move == "L":
            head -= 1

    return SimulationOutcome("TIMEOUT", _trim(cells, blank), max_steps, history)


def trace(
    machine: TuringMachineSpec,
    tape: str | None = None,
    max_steps: int = 10_000,
) -> Iterator[SimulationStep]:
    """Yield each configuration of the machine until it halts or times out."""
    outcome = simulate(machine, tape, max_steps, record_history=True)
    yield from outcome.history


def _trim(cells: list[str], blank: str) -> str:
    return "".join(cells).strip(blank)

"""quantum.py — Quantum Turing machine simulator.

The machine state is a wavefunction: a superposition of classical
configurations (internal_state, tape, head), each carrying a complex
amplitude.  Each simulation step applies quantum transitions — potentially
branching one configuration into many — and interference collapses
identical configurations by summing their amplitudes.

Measurement samples from |amplitude|² probabilities to yield a classical
outcome, or ``measurement_outcomes`` lists all outcomes with their
probabilities without collapsing.

Author:  Taylor Moon <taylorcmoon>
License: Proprietary — All Rights Reserved
"""
from __future__ import annotations

import cmath
import math
import random
from typing import Iterator

from .types import (
    Configuration ,
    QMeasurementOutcome ,
    QSimulationOutcome ,
    QSimulationStep ,
    QTransition ,
    QTuringMachineSpec ,
    SimResult ,
    Wavefunction ,
)

# Amplitudes below this magnitude are pruned (floating-point noise)
_ZERO_THRESHOLD = 1e-12


# ---------------------------------------------------------------------------
# Core wavefunction operations
# ---------------------------------------------------------------------------

def normalise ( wf: Wavefunction ) -> Wavefunction:
    """Return a copy of wf scaled so Σ|αᵢ|² = 1."""
    norm = math.sqrt ( sum ( abs ( a ) ** 2 for a in wf.values ( ) ) )
    if norm < _ZERO_THRESHOLD:
        return dict ( wf )
    return {cfg: a / norm for cfg , a in wf.items ( )}


def probabilities ( wf: Wavefunction ) -> dict[ Configuration , float ]:
    """Return |αᵢ|² for every basis state in the wavefunction."""
    return {cfg: abs ( a ) ** 2 for cfg , a in wf.items ( )}


def inner_product ( wf_a: Wavefunction , wf_b: Wavefunction ) -> complex:
    """Compute ⟨ψ_a|ψ_b⟩ = Σ conj(α_a) · α_b over shared configurations."""
    return sum (
        wf_a[ cfg ].conjugate ( ) * wf_b[ cfg ]
        for cfg in wf_a
        if cfg in wf_b
    )


# ---------------------------------------------------------------------------
# Single-step evolution
# ---------------------------------------------------------------------------

def _build_table (
        machine: QTuringMachineSpec ,
) -> dict[ tuple[ str , str ] , list[ QTransition ] ]:
    table: dict[ tuple[ str , str ] , list[ QTransition ] ] = {}
    for t in machine.transitions:
        table.setdefault ( (t.state , t.read) , [ ] ).append ( t )
    return table


def step ( wf: Wavefunction , machine: QTuringMachineSpec ) -> Wavefunction:
    """Evolve the wavefunction by one quantum step.

    For each basis state (s, tape, h) with amplitude α:
    - If s is a halt state, carry it forward unchanged.
    - Otherwise look up all matching QTransitions for (s, tape[h]).
    - Each transition t produces a new configuration with amplitude α · t.amplitude.
    Amplitudes for identical output configurations interfere (sum).
    """
    blank = machine.blank_symbol
    table = _build_table ( machine )
    halt = {machine.accept_state , machine.reject_state}
    new_wf: Wavefunction = {}

    for (state , tape , head) , amp in wf.items ( ):
        if state in halt:
            new_wf[ (state , tape , head) ] = new_wf.get ( (state , tape , head) , 0j ) + amp
            continue

        # Extend tape so head index is valid
        tape_list = list ( tape )
        while head < 0:
            tape_list.insert ( 0 , blank )
            head = 0
        while head >= len ( tape_list ):
            tape_list.append ( blank )
        tape = tuple ( tape_list )

        sym = tape[ head ]
        branches = table.get ( (state , sym) )

        if not branches:
            # No rule → reject branch
            key: Configuration = (machine.reject_state , tape , head)
            new_wf[ key ] = new_wf.get ( key , 0j ) + amp
            continue

        for t in branches:
            new_tape = list ( tape )
            new_tape[ head ] = t.write
            new_head = head + (1 if t.move == "R" else -1 if t.move == "L" else 0)
            key = (t.next_state , tuple ( new_tape ) , new_head)
            new_wf[ key ] = new_wf.get ( key , 0j ) + amp * t.amplitude

    # Prune floating-point noise
    return {cfg: a for cfg , a in new_wf.items ( ) if abs ( a ) > _ZERO_THRESHOLD}


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def simulate (
        machine: QTuringMachineSpec ,
        tape: str | None = None ,
        max_steps: int = 1_000 ,
        record_history: bool = False ,
) -> QSimulationOutcome:
    """Run the QTM until all branches halt or max_steps is reached.

    Parameters
    ----------
    machine:
        The quantum Turing machine specification.
    tape:
        Initial tape string.  Defaults to ``machine.input_tape``.
    max_steps:
        Hard limit on evolution steps.
    record_history:
        If True, store the full wavefunction at every step.

    Returns
    -------
    QSimulationOutcome
        Includes the most-probable classical outcome and the full
        probability distribution over all outcomes.
    """
    blank = machine.blank_symbol
    tape_str = tape if tape is not None else machine.input_tape
    initial_tape = tuple ( tape_str ) if tape_str else (blank ,)

    wf: Wavefunction = {(machine.start_state , initial_tape , 0): 1.0 + 0j}
    history: list[ QSimulationStep ] = [ ]
    halt = {machine.accept_state , machine.reject_state}
    steps_taken = 0

    if record_history:
        history.append ( QSimulationStep ( step=0 , wavefunction=dict ( wf ) ) )

    for s in range ( 1 , max_steps + 1 ):
        if all ( state in halt for state , _ , _ in wf ):
            break
        wf = step ( wf , machine )
        steps_taken = s
        if record_history:
            history.append ( QSimulationStep ( step=s , wavefunction=dict ( wf ) ) )

    outcomes = _measurement_outcomes ( wf , machine , blank )
    if outcomes:
        best = outcomes[ 0 ]
        result: SimResult = best.result
        final_tape = best.final_tape
    else:
        result = "TIMEOUT"
        final_tape = ""

    return QSimulationOutcome (
        result=result ,
        final_tape=final_tape ,
        steps=steps_taken ,
        history=history ,
        measurement_outcomes=outcomes ,
    )


def trace (
        machine: QTuringMachineSpec ,
        tape: str | None = None ,
        max_steps: int = 1_000 ,
) -> Iterator[ QSimulationStep ]:
    """Yield the wavefunction at each step lazily."""
    blank = machine.blank_symbol
    tape_str = tape if tape is not None else machine.input_tape
    initial_tape = tuple ( tape_str ) if tape_str else (blank ,)
    wf: Wavefunction = {(machine.start_state , initial_tape , 0): 1.0 + 0j}
    halt = {machine.accept_state , machine.reject_state}

    yield QSimulationStep ( step=0 , wavefunction=dict ( wf ) )
    for s in range ( 1 , max_steps + 1 ):
        if all ( state in halt for state , _ , _ in wf ):
            break
        wf = step ( wf , machine )
        yield QSimulationStep ( step=s , wavefunction=dict ( wf ) )


# ---------------------------------------------------------------------------
# Measurement
# ---------------------------------------------------------------------------

def _measurement_outcomes (
        wf: Wavefunction ,
        machine: QTuringMachineSpec ,
        blank: str ,
) -> list[ QMeasurementOutcome ]:
    """Group wavefunction branches by (result_label, trimmed_tape) and sum probabilities."""
    groups: dict[ tuple[ str , str ] , float ] = {}
    for (state , tape , _) , amp in wf.items ( ):
        tape_str = "".join ( tape ).strip ( blank )
        if state == machine.accept_state:
            label: SimResult = "ACCEPT"
        elif state == machine.reject_state:
            label = "REJECT"
        else:
            label = "TIMEOUT"
        key = (label , tape_str)
        groups[ key ] = groups.get ( key , 0.0 ) + abs ( amp ) ** 2

    return sorted (
        [ QMeasurementOutcome ( result=label , final_tape=t , probability=p )
          for (label , t) , p in groups.items ( ) ] ,
        key=lambda o: -o.probability ,
    )


def measure_once ( wf: Wavefunction ) -> Configuration:
    """Sample one configuration from the wavefunction (simulates physical measurement)."""
    configs = list ( wf )
    weights = [ abs ( wf[ c ] ) ** 2 for c in configs ]
    total = sum ( weights )
    (chosen ,) = random.choices ( configs , weights=[ w / total for w in weights ] )
    return chosen


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def hadamard_amplitude ( ) -> complex:
    """Return 1/√2 — the H89+adamard amplitude for equal superposition."""
    return 1.0 / math.sqrt ( 2 ) + 0j


def phase ( theta: float ) -> complex:
    """Return e^(iθ) — a pure phase factor."""
    return cmath.exp ( 1j * theta )

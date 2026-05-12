"""wolfram.py — Wolfram Language code generation for Turing machines.

``to_wolfram()`` renders a ``TuringMachineSpec`` as a Wolfram Language
association literal ready for use in a Wolfram notebook or WolframCloud deployment.

Author:  Taylor Moon <taylorcmoon>
License: Proprietary — All Rights Reserved
"""
from __future__ import annotations

from .types import TuringMachineSpec


def to_wolfram(machine: TuringMachineSpec) -> str:
    """Render the machine as a Wolfram Language association literal."""
    transitions = ",\n  ".join(
        f'{{"{t.state}", "{t.read}"}} -> '
        f'{{"{t.next_state}", "{t.write}", "{t.move}"}}'
        for t in machine.transitions
    )
    alphabet = ", ".join(f'"{s}"' for s in machine.alphabet)

    return (
        f"(* {machine.name} *)\n"
        "machine = <|\n"
        f'  "Alphabet" -> {{{alphabet}}},\n'
        f'  "BlankSymbol" -> "{machine.blank_symbol}",\n'
        f'  "StartState" -> "{machine.start_state}",\n'
        f'  "AcceptState" -> "{machine.accept_state}",\n'
        f'  "RejectState" -> "{machine.reject_state}",\n'
        '  "Transitions" -> {\n'
        f"  {transitions}\n"
        "  }\n"
        "|>;\n\n"
        f'inputTape = Characters["{machine.input_tape}"];\n\n'
        "(* Adapt this association into your preferred Wolfram Language Turing machine simulator. *)\n"
        "Dataset[machine]"
    )

"""presets.py — built-in machines, workspace commands, and modeling presets.

Exports:
- ``STARTER_MACHINE`` — a binary incrementer to use as a starting point
- ``WORKSPACE_COMMANDS`` — template Wolfram Language snippets
- ``MODELING_PRESETS`` — categorised research starting points

Author:  Taylor Moon <taylorcmoon>
License: MIT
"""
from __future__ import annotations

from .types import ModelingPreset, Transition, TuringMachineSpec, WorkspaceCommand

STARTER_MACHINE = TuringMachineSpec(
    name="Binary Incrementer Draft",
    alphabet=["0", "1", "_"],
    blank_symbol="_",
    start_state="q0",
    accept_state="qAccept",
    reject_state="qReject",
    input_tape="1011",
    transitions=[
        Transition(id="t1", state="q0", read="1", write="0", move="L", next_state="q0"),
        Transition(id="t2", state="q0", read="0", write="1", move="S", next_state="qAccept"),
        Transition(id="t3", state="q0", read="_", write="1", move="S", next_state="qAccept"),
    ],
)


WORKSPACE_COMMANDS: list[WorkspaceCommand] = [
    WorkspaceCommand(
        id="tm-sim",
        title="Bounded Turing Machine Simulation",
        description="Template for sending a transition system to Wolfram Language for inspection.",
        code='states = {"q0", "qAccept", "qReject"};\n'
        'alphabet = {"0", "1", "_"};\n'
        'input = Characters["1011"];\n\n'
        "transitionGraph = Graph[\n"
        '  {"q0" -> "q0", "q0" -> "qAccept"},\n'
        '  VertexLabels -> "Name",\n'
        '  GraphLayout -> "LayeredDigraphEmbedding"\n'
        "];\n\n"
        "transitionGraph",
    ),
    WorkspaceCommand(
        id="cellular",
        title="Cellular Automaton Explorer",
        description="Use Wolfram's cellular automata tools to model simple computational systems.",
        code="rule = 110;\n"
        "steps = 80;\n"
        "initial = CenterArray[{1}, 161];\n\n"
        "ArrayPlot[\n"
        "  CellularAutomaton[rule, initial, steps],\n"
        "  PixelConstrained -> 4\n"
        "]",
    ),
    WorkspaceCommand(
        id="graph-model",
        title="State Graph Model",
        description="Represent system states as graph vertices and transitions as directed edges.",
        code="model = Graph[\n"
        '  {"Start" -> "Scan", "Scan" -> "Rewrite", "Rewrite" -> "Move", '
        '"Move" -> "Scan", "Scan" -> "Halt"},\n'
        '  VertexLabels -> "Name",\n'
        '  GraphLayout -> "SpringElectricalEmbedding"\n'
        "];\n\n"
        '{model, FindPath[model, "Start", "Halt"]}',
    ),
]


MODELING_PRESETS: list[ModelingPreset] = [
    ModelingPreset(
        id="busy-beaver",
        title="Busy Beaver Research",
        category="automata",
        description="Draft transition tables, compare halting behavior, and visualize state graphs.",
        wolfram_code="(* Busy Beaver style transition analysis *)\n"
        'states = {"A", "B", "HALT"};\n'
        'edges = {"A" -> "B", "B" -> "A", "B" -> "HALT"};\n'
        'Graph[edges, VertexLabels -> "Name"]',
    ),
    ModelingPreset(
        id="rewriting-system",
        title="Symbolic Rewriting System",
        category="systems",
        description="Model rule-based systems that transform strings, tapes, or symbolic expressions.",
        wolfram_code='rules = {"AB" -> "BA", "AA" -> "B"};\n'
        'NestList[StringReplace[#, rules] &, "AAB", 8]',
    ),
    ModelingPreset(
        id="network-dynamics",
        title="Network Dynamics",
        category="dynamics",
        description="Explore how local transition rules produce global behavior over a graph.",
        wolfram_code='g = RandomGraph[{12, 20}, VertexLabels -> "Name"];\n'
        "{g, AdjacencyMatrix[g] // MatrixPlot}",
    ),
    ModelingPreset(
        id="finite-automaton",
        title="Finite Automaton Sketch",
        category="automata",
        description="Prototype state-machine structure before expanding into a Turing machine.",
        wolfram_code="Graph[\n"
        '  {"q0" -> "q1", "q1" -> "q2", "q2" -> "q1", "q2" -> "accept"},\n'
        '  VertexLabels -> "Name",\n'
        '  GraphLayout -> "LayeredDigraphEmbedding"\n'
        "]",
    ),
]

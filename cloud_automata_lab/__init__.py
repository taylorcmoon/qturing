"""Cloud Automata Lab — design Turing machines and model computational systems.

Provides dataclass-based machine specs, a local simulator, Wolfram Language
code generation, multi-language exporters (Python / JavaScript / Go / C / Wolfram),
a WolframCloud client with mock mode, and workspace presets.

Author:  Taylor Moon <taylorcmoon>
License: Proprietary — All Rights Reserved
Source:  https://github.com/taylorcmoon/Quasilink
"""

from .cloud import execute
from .exporters import EXPORT_LANGUAGES, ExportLanguage, export
from .presets import MODELING_PRESETS, STARTER_MACHINE, WORKSPACE_COMMANDS
from .quantum import (
    hadamard_amplitude,
    inner_product,
    measure_once,
    normalise,
    phase,
    probabilities,
    simulate as q_simulate,
    trace as q_trace,
)
from .turing import SimulationOutcome, SimulationStep, simulate, trace
from .types import (
    CloudRequest,
    CloudResponse,
    CloudSettings,
    Configuration,
    ExecutionMode,
    ModelingPreset,
    Move,
    PresetCategory,
    QMeasurementOutcome,
    QSimulationOutcome,
    QSimulationStep,
    QTransition,
    QTuringMachineSpec,
    Transition,
    TuringMachineSpec,
    Wavefunction,
    WorkspaceCommand,
)
from .wolfram import to_wolfram

__all__ = [
    # Classical TM
    "CloudRequest",
    "CloudResponse",
    "CloudSettings",
    "EXPORT_LANGUAGES",
    "ExecutionMode",
    "ExportLanguage",
    "MODELING_PRESETS",
    "ModelingPreset",
    "Move",
    "PresetCategory",
    "STARTER_MACHINE",
    "SimulationOutcome",
    "SimulationStep",
    "Transition",
    "TuringMachineSpec",
    "WORKSPACE_COMMANDS",
    "WorkspaceCommand",
    "execute",
    "export",
    "simulate",
    "to_wolfram",
    "trace",
    # Quantum TM
    "Configuration",
    "QMeasurementOutcome",
    "QSimulationOutcome",
    "QSimulationStep",
    "QTransition",
    "QTuringMachineSpec",
    "Wavefunction",
    "hadamard_amplitude",
    "inner_product",
    "measure_once",
    "normalise",
    "phase",
    "probabilities",
    "q_simulate",
    "q_trace",
]

"""Cloud Automata Lab — design Turing machines and model computational systems.

Provides dataclass-based machine specs, a local simulator, Wolfram Language
code generation, multi-language exporters (Python / JavaScript / Go / C / Wolfram),
a WolframCloud client with mock mode, and workspace presets.

Author:  Taylor Moon <taylorcmoon>
License: MIT
Source:  https://github.com/taylorcmoon/Quasilink
"""

from .cloud import execute
from .exporters import EXPORT_LANGUAGES, ExportLanguage, export
from .presets import MODELING_PRESETS, STARTER_MACHINE, WORKSPACE_COMMANDS
from .turing import SimulationOutcome, SimulationStep, simulate, trace
from .types import (
    CloudRequest,
    CloudResponse,
    CloudSettings,
    ExecutionMode,
    ModelingPreset,
    Move,
    PresetCategory,
    Transition,
    TuringMachineSpec,
    WorkspaceCommand,
)
from .wolfram import to_wolfram

__all__ = [
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
]

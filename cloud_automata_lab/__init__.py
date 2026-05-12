"""Cloud Automata Lab — design Turing machines and model computational systems.

Python port of the WolframCloud-style frontend originally specified in
``CloudAutomataLabFrontend.md``. Provides:

- dataclass-based machine specs (``TuringMachineSpec``, ``Transition``)
- a local simulator (``simulate``, ``trace``)
- Wolfram Language code generation (``to_wolfram``)
- multi-language exporters (Python / JavaScript / Go / Wolfram)
- a WolframCloud client with a mock mode (``execute``)
- workspace commands and modeling presets
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

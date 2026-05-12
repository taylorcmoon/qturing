# Cloud Automata Lab

Design Turing machines, explore cellular automata, and dispatch Wolfram Language
code to WolframCloud — all from Python.

**Author:** Taylor Moon  
**License:** Proprietary — All Rights Reserved  
**Source:** https://github.com/taylorcmoon/Quasilink

---

## Requirements

- Python 3.10 or later
- A [Wolfram ID](https://account.wolfram.com) (free) for live cloud execution

---

## Install

Clone the repo and install in one step:

```bash
git clone https://github.com/taylorcmoon/Quasilink.git
cd Quasilink
pip install -e .
```

This automatically installs the `wolframclient` dependency.

---

## Quick start

```python
from cloud_automata_lab import (
    STARTER_MACHINE,
    CloudRequest,
    CloudSettings,
    execute,
    export,
    simulate,
    to_wolfram,
)

# Run the simulator locally
outcome = simulate(STARTER_MACHINE)
print(outcome.result, outcome.final_tape)

# Export to any language
print(export(STARTER_MACHINE, "python"))
print(export(STARTER_MACHINE, "c"))

# Send to WolframCloud (mock mode — no credentials needed)
settings = CloudSettings(mode="mock")
response = execute(settings, CloudRequest(code=to_wolfram(STARTER_MACHINE)))
print(response.result)
```

---

## WolframCloud (live mode)

Sign up for a free Wolfram ID at https://account.wolfram.com, then:

```python
settings = CloudSettings(
    mode="live",
    wolfram_id="your@email.com",
    wolfram_password="your-password",
)
response = execute(settings, CloudRequest(code="Range[10]"))
print(response.result)
```

---

## Exporting a machine

```python
from cloud_automata_lab import STARTER_MACHINE, export

# Available: "wolfram", "python", "javascript", "go", "c"
code = export(STARTER_MACHINE, "c")
with open("tm.c", "w") as f:
    f.write(code)
```

Compile and run the C export:

```bash
cc -O2 -o tm tm.c && ./tm
```

---

## API reference

| Symbol | Purpose |
|---|---|
| `TuringMachineSpec`, `Transition` | Machine data model |
| `simulate`, `trace`, `SimulationOutcome` | Local simulator |
| `to_wolfram` | Wolfram Language code generation |
| `export`, `EXPORT_LANGUAGES` | Wolfram / Python / JavaScript / Go / C exporters |
| `execute`, `CloudSettings`, `CloudRequest`, `CloudResponse` | WolframCloud client |
| `STARTER_MACHINE`, `WORKSPACE_COMMANDS`, `MODELING_PRESETS` | Built-in templates |
| `CARule`, `CAConfig`, `run`, `trace_1d` | 1D cellular automaton engine |
| `CA2DConfig`, `run_2d`, `trace_2d` | 2D cellular automaton engine |

---

## Run tests

```bash
pip install -e ".[dev]"
pytest tests/
```

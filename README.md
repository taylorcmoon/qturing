# cloud-automata-lab

A Python port of the **Cloud Automata Lab** frontend specification. Design Turing
machines, model computational systems, and dispatch Wolfram Language code to a
WolframCloud endpoint — all from regular Python.

This is the library form of `src/CloudAutomataLabFrontend.md`. The React app
keeps the GUI; this package keeps the data model, the simulator, the code
generators, and the cloud client.

## Install

```bash
pip install -e libs/cloud_automata_lab
```

No third-party dependencies — stdlib only.

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

outcome = simulate(STARTER_MACHINE)
print(outcome.result, outcome.final_tape, outcome.steps)

print(to_wolfram(STARTER_MACHINE))
print(export(STARTER_MACHINE, "go"))

settings = CloudSettings(mode="mock")
response = execute(settings, CloudRequest(code=to_wolfram(STARTER_MACHINE)))
print(response.result)
```

## Public API

| Symbol | Purpose |
| --- | --- |
| `TuringMachineSpec`, `Transition` | Machine data model |
| `simulate`, `trace`, `SimulationOutcome` | Local simulator |
| `to_wolfram` | Wolfram Language code generation |
| `export`, `EXPORT_LANGUAGES` | Wolfram / Python / JavaScript / Go exporters |
| `execute`, `CloudSettings`, `CloudRequest`, `CloudResponse` | WolframCloud client (mock + HTTP) |
| `STARTER_MACHINE`, `WORKSPACE_COMMANDS`, `MODELING_PRESETS` | Built-in templates |

## WolframCloud endpoint contract

`execute()` POSTs JSON of the form:

```json
{
  "code": "...",
  "parameters": { ... }
}
```

…with optional `Authorization: Bearer <api_key>`. A response shape of
`{"result": "..."}` is parsed; otherwise the raw body is returned in
`CloudResponse.raw`.

## Tests

```bash
python -m pytest libs/cloud_automata_lab/tests
```

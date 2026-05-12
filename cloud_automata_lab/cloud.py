"""cloud.py — WolframCloud HTTP client with mock mode.

``execute()`` sends a ``CloudRequest`` to a WolframCloud endpoint and returns
a ``CloudResponse``. Set ``CloudSettings.mode`` to ``"mock"`` during
development to get realistic stub responses without a live endpoint.

Author:  Taylor Moon <taylorcmoon>
License: MIT
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from .types import CloudRequest, CloudResponse, CloudSettings


def execute(
    settings: CloudSettings,
    request: CloudRequest,
    *,
    timeout: float = 30.0,
    mock_delay: float = 0.0,
) -> CloudResponse:
    """Send a request to a WolframCloud endpoint, or return a mock result."""
    if settings.mode == "mock":
        if mock_delay > 0:
            time.sleep(mock_delay)
        return CloudResponse(
            ok=True,
            result=_mock_result(request.code),
            executed_at=_now(),
        )

    if not settings.endpoint_url.strip():
        return CloudResponse(
            ok=False,
            result="",
            error="Missing WolframCloud endpoint URL.",
            executed_at=_now(),
        )

    payload = json.dumps(
        {"code": request.code, "parameters": request.parameters or {}}
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if settings.api_key:
        headers["Authorization"] = f"Bearer {settings.api_key}"

    req = urllib.request.Request(
        settings.endpoint_url, data=payload, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        status = exc.code
    except urllib.error.URLError as exc:
        return CloudResponse(
            ok=False,
            result="",
            error=str(exc.reason),
            executed_at=_now(),
        )

    try:
        raw: object = json.loads(text)
    except ValueError:
        raw = text

    if isinstance(raw, dict) and "result" in raw:
        result_text = str(raw["result"])
    else:
        result_text = text

    ok = 200 <= status < 300
    return CloudResponse(
        ok=ok,
        result=result_text if ok else "",
        raw=raw,
        error=None if ok else f"HTTP {status}",
        executed_at=_now(),
    )


def _mock_result(code: str) -> str:
    if "TuringMachine" in code:
        return (
            "Mock WolframCloud Result\n\n"
            "Turing machine analysis completed.\n"
            "States detected: q0, qAccept, qReject\n"
            "Computation class: deterministic single-tape model\n"
            "Suggested next step: export transition graph or run bounded simulation."
        )
    if "CellularAutomaton" in code:
        return (
            "Mock WolframCloud Result\n\n"
            "Cellular automaton generated.\n"
            "Useful Wolfram functions:\n"
            "- CellularAutomaton\n"
            "- ArrayPlot\n"
            "- RulePlot"
        )
    if "Graph" in code:
        return (
            "Mock WolframCloud Result\n\n"
            "Graph/model structure evaluated.\n"
            "Suggested operations:\n"
            "- FindPath\n"
            "- GraphPlot\n"
            "- VertexDegree\n"
            "- ConnectedComponents"
        )
    return (
        "Mock WolframCloud Result\n\n"
        "Expression accepted.\n"
        "This local mock mode lets you design commands before connecting a real "
        "WolframCloud endpoint.\n\n"
        "Submitted code:\n" + code
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

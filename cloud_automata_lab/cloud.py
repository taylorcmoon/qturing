"""cloud.py — WolframCloud client with mock mode.

``execute()`` sends a ``CloudRequest`` to WolframCloud and returns a
``CloudResponse``. Uses the official ``wolframclient`` library in live mode.
Set ``CloudSettings.mode`` to ``"mock"`` during development to get realistic
stub responses without credentials.

Author:  Taylor Moon <taylorcmoon>
License: Proprietary — All Rights Reserved
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from .types import CloudRequest, CloudResponse, CloudSettings


def execute(
    settings: CloudSettings,
    request: CloudRequest,
    *,
    timeout: float = 30.0,
    mock_delay: float = 0.0,
) -> CloudResponse:
    """Send a request to WolframCloud, or return a mock result.

    In live mode, authenticates via ``wolfram_id`` / ``wolfram_password`` on
    ``CloudSettings`` using the official ``wolframclient`` library.
    """
    if settings.mode == "mock":
        if mock_delay > 0:
            time.sleep(mock_delay)
        return CloudResponse(
            ok=True,
            result=_mock_result(request.code),
            executed_at=_now(),
        )

    return _execute_live(settings, request, timeout=timeout)


def _execute_live(
    settings: CloudSettings,
    request: CloudRequest,
    *,
    timeout: float,
) -> CloudResponse:
    try:
        from wolframclient.evaluation import WolframCloudSession
        from wolframclient.language import wlexpr
    except ImportError:
        return CloudResponse(
            ok=False,
            result="",
            error="wolframclient is not installed. Run: pip install wolframclient",
            executed_at=_now(),
        )

    if not settings.wolfram_id or not settings.wolfram_password:
        return CloudResponse(
            ok=False,
            result="",
            error="Set wolfram_id and wolfram_password on CloudSettings to use live mode.",
            executed_at=_now(),
        )

    try:
        session = WolframCloudSession(
            credentials=(settings.wolfram_id, settings.wolfram_password)
        )
        session.start()
        result = session.evaluate(wlexpr(request.code))
        session.stop()
        return CloudResponse(
            ok=True,
            result=str(result),
            raw=result,
            executed_at=_now(),
        )
    except Exception as exc:
        return CloudResponse(
            ok=False,
            result="",
            error=str(exc),
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

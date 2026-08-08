"""
PC Slowdown Diagnoser — FastAPI Backend
========================================
Single endpoint: POST /diagnose
- Accepts collector JSON
- Runs the deterministic rules engine
- Returns prioritized issues list

Run locally:
    uvicorn main:app --reload --port 8000

Test:
    curl -X POST http://localhost:8000/diagnose \
         -H "Content-Type: application/json" \
         -d @../collector/report.json
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Make rules_engine importable from sibling directory
# ---------------------------------------------------------------------------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from rules_engine.engine import diagnose  # noqa: E402

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="PC Slowdown Diagnoser API",
    description=(
        "Accepts a system telemetry JSON collected by the collector script "
        "and returns a prioritised list of performance issues with fixes."
    ),
    version="0.1.0",
)

# Allow the Next.js frontend (any origin during dev; tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CollectorReport(BaseModel):
    """
    Loosely typed model — we accept the full collector JSON as-is.
    All fields are optional so the engine can handle partial/future reports.
    """
    model_config = {"extra": "allow"}

    collected_at: str | None = None
    cpu: dict[str, Any] | None = None
    ram: dict[str, Any] | None = None
    disk: dict[str, Any] | None = None
    startup: dict[str, Any] | None = None
    os: dict[str, Any] | None = None
    background: dict[str, Any] | None = None

    @field_validator("cpu", "ram", "disk", "startup", "os", "background", mode="before")
    @classmethod
    def must_be_dict_or_none(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError("Field must be a JSON object or null")
        return v


class Issue(BaseModel):
    issue: str
    severity: str
    evidence: str
    fix: str
    top_offenders: list[str]


class DiagnoseResponse(BaseModel):
    collected_at: str | None
    issue_count: int
    issues: list[Issue]
    engine_version: str = "0.1.0"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", summary="Health check")
def root():
    """Simple health check — confirms the API is running."""
    return {"status": "ok", "service": "pc-slowdown-diagnoser"}


@app.post(
    "/diagnose",
    response_model=DiagnoseResponse,
    summary="Diagnose a system report",
    response_description="Prioritised list of performance issues (high → low)",
)
def diagnose_report(report: CollectorReport):
    """
    Accept a collector JSON report and run the deterministic rules engine.

    Returns a prioritised list of issues — no AI calls, fully deterministic.
    The LLM rewrite step will be layered on top in a later version.
    """
    try:
        raw = report.model_dump()
        issues = diagnose(raw)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Rules engine error: {exc}") from exc

    return DiagnoseResponse(
        collected_at=report.collected_at,
        issue_count=len(issues),
        issues=issues,
    )


# ---------------------------------------------------------------------------
# Request timing middleware (helpful for debugging)
# ---------------------------------------------------------------------------

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-Ms"] = str(elapsed)
    return response


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

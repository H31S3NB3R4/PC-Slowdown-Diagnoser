"""
PC Slowdown Diagnoser — FastAPI Backend
========================================
Single endpoint: POST /diagnose
- Accepts collector JSON
- Runs the deterministic rules engine
- Optionally rewrites issues via Gemini LLM for plain-English output
- Returns prioritized issues list

Run locally:
    uvicorn main:app --reload --port 8000

Test (raw engine output):
    curl -X POST http://localhost:8000/diagnose \
         -H "Content-Type: application/json" \
         -d @../collector/report.json

Test (with LLM rewrite):
    curl -X POST "http://localhost:8000/diagnose?rewrite=true" \
         -H "Content-Type: application/json" \
         -d @../collector/report.json
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

# Load .env (for GEMINI_API_KEY)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ---------------------------------------------------------------------------
# Make rules_engine and llm_rewriter importable regardless of working dir
# ---------------------------------------------------------------------------
_BACKEND = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_BACKEND)
for _p in (_ROOT, _BACKEND):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rules_engine.engine import diagnose  # noqa: E402
from llm_rewriter import rewrite_issues  # noqa: E402

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
    rewritten: bool = False
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
def diagnose_report(
    report: CollectorReport,
    rewrite: bool = Query(
        False,
        description=(
            "If true, pass the rules engine output through the Gemini LLM "
            "to rewrite issues in plain, friendly English."
        ),
    ),
):
    """
    Accept a collector JSON report and run the deterministic rules engine.

    If `rewrite=true`, the issues are passed through the Gemini LLM for
    plain-English rewrites. The LLM never changes severity, evidence, or
    offenders — it only rephrases the issue headline and fix text.
    Falls back to raw engine output if the LLM call fails.
    """
    try:
        raw = report.model_dump()
        issues = diagnose(raw)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Rules engine error: {exc}") from exc

    rewritten = False
    if rewrite and issues:
        original_issues = issues
        issues = rewrite_issues(issues)
        rewritten = issues is not original_issues  # True only if LLM ran successfully

    return DiagnoseResponse(
        collected_at=report.collected_at,
        issue_count=len(issues),
        issues=issues,
        rewritten=rewritten,
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

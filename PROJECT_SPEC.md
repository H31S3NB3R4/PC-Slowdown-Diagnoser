# PC Slowdown Diagnoser — Project Spec

## Problem
Non-technical users don't understand why their computer is slow. They need a tool that collects system info, diagnoses bottlenecks, and gives prioritized, plain-English fixes.

## Core Principle (IMPORTANT — follow strictly)
Do NOT use an LLM to diagnose the system. Use a deterministic rules engine for diagnosis (reliable, free, testable). Use the LLM ONLY as a final step to rewrite the rules engine's output into friendly, plain-English explanations. This keeps the app cheap, fast, and reproducible.

## Architecture
```
[Collector Script] --JSON--> [FastAPI Backend]
                                  |
                          [Rules Engine (pure code)]
                                  |
                          [LLM rewrite step] (1 call, bounded input)
                                  |
                              [Next.js UI]
```

## Scope — MVP only
Build in this order. Each step must work standalone before moving to the next.

### Step 1 — Collector Script
- Language: Python
- Target OS: Windows first
- Collects and outputs a single JSON file with:
  - CPU: model, usage %, temp (if available)
  - RAM: total, used %, top 5 processes by RAM usage
  - Disk: free space %, type (SSD/HDD), read/write speed
  - Startup programs: count + list
  - OS version, uptime, pending updates count
  - Background processes: count, top 5 by CPU
- No network calls in this script. Just collect + write JSON to disk.
- Package as `.exe` via PyInstaller once script is tested.

**Done when:** running the script produces a clean, valid JSON file with all fields populated, tested on at least 2 real machines (one "healthy," one "slow").

### Step 2 — Rules Engine
- Pure Python function: `diagnose(report: dict) -> list[dict]`
- Input: the JSON from Step 1
- Output: list of issues, each with:
  ```json
  {
    "issue": "RAM nearly full",
    "severity": "high | medium | low",
    "evidence": "92% RAM used",
    "fix": "Close unused browser tabs / uninstall unused startup apps",
    "top_offenders": ["chrome.exe", "teams.exe"]
  }
  ```
- Start with ~10-15 threshold-based rules covering: RAM, disk space, disk type, startup program count, background process count, pending updates, uptime.
- Sort output by severity (high → low).
- No AI/API calls in this file at all.

**Done when:** unit tests pass against 3-4 hand-crafted sample JSON reports representing different failure scenarios (healthy, low RAM, full disk, too many startup apps).

### Step 3 — Backend API
- Framework: FastAPI
- Single endpoint: `POST /diagnose`
  - Accepts the collector's JSON
  - Runs Step 2's rules engine
  - Returns the raw issues list (LLM step added later)
- Test with curl/Postman before touching the frontend.

**Done when:** endpoint returns correct prioritized issues list for a given JSON input, matching rules engine unit tests.

### Step 4 — LLM Rewrite Step
- Add AFTER Step 3 works.
- One LLM call per report. Input = rules engine output (NOT raw telemetry).
- Prompt constraint: rewrite each issue as 1-2 plain-English sentences, keep the same order and severity, do not invent new issues, do not change evidence/fix substance.
- This is the only place an LLM API is called in the whole app.

**Done when:** LLM output preserves all issues from the rules engine, just in friendlier language — no added/dropped/reordered issues.

### Step 5 — Frontend
- Framework: Next.js + Tailwind
- No auth needed for MVP
- Single page: upload button (accepts the JSON file, or triggers collector download) → results list showing severity-tagged, prioritized fixes
- Group/color by severity (high/medium/low)

**Done when:** a non-technical user can upload their report and get a readable, prioritized list of fixes with zero explanation needed.

## Explicitly Out of Scope for MVP
- Auto-fixing issues
- Background/continuous monitoring
- macOS/Linux support
- Native GUI app (browser upload is fine)
- User accounts / auth
- Historical tracking of reports over time

## Stack Summary
| Layer | Choice |
|---|---|
| Collector | Python → PyInstaller .exe |
| Backend | FastAPI |
| Rules Engine | Plain Python, no dependencies on AI |
| LLM step | Single bounded API call, JSON in/out |
| Frontend | Next.js + Tailwind |
| Hosting | Backend: Render/Railway free tier. Frontend: Vercel |

## Build Order for Agent
1. Scaffold collector script, test locally, confirm clean JSON output
2. Write rules engine + unit tests against sample JSON fixtures
3. Wire rules engine into FastAPI endpoint, test via curl
4. Add LLM rewrite step with strict prompt constraints above
5. Build upload + results UI

Do not skip ahead to the frontend or LLM step until the rules engine has passing tests. The rules engine is the core product value — prioritize correctness there over UI polish.

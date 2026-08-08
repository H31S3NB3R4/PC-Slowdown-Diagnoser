"""
PC Slowdown Diagnoser — LLM Rewrite Step (Gemini)
===================================================
This module is the ONLY place in the entire app where an LLM is called.

Contract (strict, per spec):
  - Input:  the raw issues list produced by the rules engine
  - Output: the same list, in the same order, with the same severity/evidence/fix
            substance — but with `issue` and `fix` rewritten in plain English
  - One API call per report (all issues batched in a single prompt)
  - If the LLM call fails for any reason, the original rules engine output
    is returned unchanged (graceful degradation)
  - The LLM MUST NOT add, remove, or reorder issues
"""

from __future__ import annotations

import json
import os
from typing import Any

from google import genai
from google.genai import types


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_MODEL = "gemini-2.5-flash"

_SYSTEM_PROMPT = """\
You are a friendly PC support assistant. You will receive a JSON list of \
technical performance issues found on a user's computer.

Your job is to rewrite each issue's "issue" and "fix" fields into plain, \
friendly English that a non-technical person can immediately understand and act on.

Rules you MUST follow:
1. Return a valid JSON array with the EXACT SAME number of items, in the EXACT SAME order.
2. Do NOT change "severity", "evidence", or "top_offenders" — copy them exactly.
3. Do NOT invent new issues. Do NOT drop any issue. Do NOT reorder them.
4. Rewrite "issue" as a short, friendly headline (max 8 words).
5. Rewrite "fix" as 1-2 plain-English sentences a grandparent could follow.
6. Do not use jargon like "RAM", "CPU", "HDD" without a brief explanation in parentheses.
7. Return ONLY the JSON array. No markdown, no commentary, no code fences.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def rewrite_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Rewrite the rules engine issues list into plain English using Gemini.

    Args:
        issues: List of issue dicts from rules_engine.engine.diagnose()

    Returns:
        The same list with 'issue' and 'fix' fields rewritten.
        Falls back to the original list if the LLM call fails or returns
        a structurally invalid response.
    """
    if not issues:
        return issues

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # No key configured — return raw engine output unchanged
        return issues

    try:
        return _call_gemini(issues, api_key)
    except Exception:
        # Graceful degradation — never let the LLM step crash the API
        return issues


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _call_gemini(
    issues: list[dict[str, Any]],
    api_key: str,
) -> list[dict[str, Any]]:
    client = genai.Client(api_key=api_key)

    user_message = (
        "Here are the issues found on this user's computer. "
        "Rewrite 'issue' and 'fix' in plain English following all the rules above.\n\n"
        + json.dumps(issues, indent=2)
    )

    response = client.models.generate_content(
        model=_MODEL,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            temperature=0.3,           # low randomness — consistent rewrites
            max_output_tokens=2048,
            response_mime_type="application/json",
        ),
    )

    rewritten = json.loads(response.text)

    # Validate the response has the correct structure
    _validate_rewrite(issues, rewritten)
    return rewritten


def _validate_rewrite(
    original: list[dict[str, Any]],
    rewritten: Any,
) -> None:
    """
    Ensure the LLM response is safe to use:
    - Must be a list
    - Must have the same number of items
    - Each item must preserve severity, evidence, top_offenders
    Raises ValueError on any violation (caller falls back to original).
    """
    if not isinstance(rewritten, list):
        raise ValueError(f"LLM returned {type(rewritten).__name__}, expected list")

    if len(rewritten) != len(original):
        raise ValueError(
            f"LLM returned {len(rewritten)} issues, expected {len(original)}"
        )

    required_preserved = {"severity", "evidence", "top_offenders"}
    for i, (orig, rewr) in enumerate(zip(original, rewritten)):
        if not isinstance(rewr, dict):
            raise ValueError(f"Issue {i} is not a dict: {rewr!r}")
        for field in required_preserved:
            if rewr.get(field) != orig.get(field):
                raise ValueError(
                    f"Issue {i}: LLM changed protected field '{field}'. "
                    f"Original: {orig.get(field)!r}, Got: {rewr.get(field)!r}"
                )

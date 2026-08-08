"""
PC Slowdown Diagnoser — Rules Engine
=====================================
Pure Python. No AI/API calls. No external dependencies.

Entry point:
    diagnose(report: dict) -> list[dict]

Each issue in the returned list has:
    {
        "issue":         str,           # short label
        "severity":      "high" | "medium" | "low",
        "evidence":      str,           # concrete metric that triggered the rule
        "fix":           str,           # plain action for the user
        "top_offenders": list[str],     # relevant process/program names (may be [])
    }

Results are sorted: high → medium → low.
"""

from __future__ import annotations

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Individual rule functions
# Each returns a dict (issue) or None if the rule does not trigger.
# ---------------------------------------------------------------------------

def _rule_ram_critical(r: dict) -> dict | None:
    used = r.get("ram", {}).get("used_percent", 0)
    if used >= 90:
        offenders = [
            p["name"]
            for p in r.get("ram", {}).get("top_processes", [])
        ]
        return {
            "issue": "RAM critically full",
            "severity": "high",
            "evidence": f"{used}% RAM in use",
            "fix": (
                "Close unused applications immediately. "
                "Consider upgrading RAM or reducing startup programs."
            ),
            "top_offenders": offenders,
        }
    return None


def _rule_ram_high(r: dict) -> dict | None:
    used = r.get("ram", {}).get("used_percent", 0)
    if 75 <= used < 90:
        offenders = [
            p["name"]
            for p in r.get("ram", {}).get("top_processes", [])
        ]
        return {
            "issue": "RAM usage high",
            "severity": "medium",
            "evidence": f"{used}% RAM in use",
            "fix": (
                "Close browser tabs or unused apps. "
                "Check for memory-hungry background programs."
            ),
            "top_offenders": offenders,
        }
    return None


def _rule_cpu_critical(r: dict) -> dict | None:
    usage = r.get("cpu", {}).get("usage_percent", 0)
    if usage >= 80:
        offenders = [
            p["name"]
            for p in r.get("background", {}).get("top_cpu_processes", [])
            if p.get("name", "").lower() not in ("system idle process",)
        ]
        return {
            "issue": "CPU overloaded",
            "severity": "high",
            "evidence": f"{usage}% CPU usage",
            "fix": (
                "End the high-CPU processes listed below, "
                "or restart your computer to clear runaway tasks."
            ),
            "top_offenders": offenders,
        }
    return None


def _rule_cpu_high(r: dict) -> dict | None:
    usage = r.get("cpu", {}).get("usage_percent", 0)
    if 60 <= usage < 80:
        offenders = [
            p["name"]
            for p in r.get("background", {}).get("top_cpu_processes", [])
            if p.get("name", "").lower() not in ("system idle process",)
        ]
        return {
            "issue": "CPU usage elevated",
            "severity": "medium",
            "evidence": f"{usage}% CPU usage",
            "fix": (
                "Check which programs are using the most CPU "
                "and close any you don't need."
            ),
            "top_offenders": offenders,
        }
    return None


def _rule_disk_space_critical(r: dict) -> dict | None:
    free = r.get("disk", {}).get("free_percent", 100)
    if free < 10:
        return {
            "issue": "Disk almost full",
            "severity": "high",
            "evidence": f"Only {free}% disk space free on C:\\",
            "fix": (
                "Delete files from Downloads and Recycle Bin, "
                "uninstall unused programs, or move files to external storage."
            ),
            "top_offenders": [],
        }
    return None


def _rule_disk_space_low(r: dict) -> dict | None:
    free = r.get("disk", {}).get("free_percent", 100)
    if 10 <= free < 20:
        return {
            "issue": "Disk space low",
            "severity": "medium",
            "evidence": f"{free}% disk space free on C:\\",
            "fix": (
                "Run Disk Cleanup (search 'Disk Cleanup' in Start), "
                "and empty the Recycle Bin."
            ),
            "top_offenders": [],
        }
    return None


def _rule_disk_type_hdd(r: dict) -> dict | None:
    disk_type = r.get("disk", {}).get("type", "Unknown")
    if disk_type == "HDD":
        return {
            "issue": "Using a slow hard drive (HDD)",
            "severity": "medium",
            "evidence": "System drive is a spinning HDD, not an SSD",
            "fix": (
                "Upgrading to an SSD is the single biggest speed improvement "
                "you can make on an older PC. It typically reduces boot time by 5×."
            ),
            "top_offenders": [],
        }
    return None


def _rule_startup_critical(r: dict) -> dict | None:
    count = r.get("startup", {}).get("count", 0)
    if count > 15:
        programs = [
            p["name"]
            for p in r.get("startup", {}).get("programs", [])
        ]
        return {
            "issue": "Too many startup programs",
            "severity": "high",
            "evidence": f"{count} programs launch automatically at startup",
            "fix": (
                "Open Task Manager → Startup tab and disable programs "
                "you don't need immediately after login."
            ),
            "top_offenders": programs,
        }
    return None


def _rule_startup_high(r: dict) -> dict | None:
    count = r.get("startup", {}).get("count", 0)
    if 8 < count <= 15:
        programs = [
            p["name"]
            for p in r.get("startup", {}).get("programs", [])
        ]
        return {
            "issue": "Many startup programs",
            "severity": "medium",
            "evidence": f"{count} programs launch automatically at startup",
            "fix": (
                "Open Task Manager → Startup tab and disable programs "
                "you don't recognize or rarely use."
            ),
            "top_offenders": programs,
        }
    return None


def _rule_background_processes(r: dict) -> dict | None:
    count = r.get("background", {}).get("process_count", 0)
    if count > 250:
        return {
            "issue": "Excessive background processes",
            "severity": "medium",
            "evidence": f"{count} processes running in the background",
            "fix": (
                "Restart your computer to clear accumulated background tasks, "
                "then reduce startup programs to prevent them re-launching."
            ),
            "top_offenders": [],
        }
    return None


def _rule_pending_updates_many(r: dict) -> dict | None:
    updates = r.get("os", {}).get("pending_updates")
    if updates is not None and updates > 10:
        return {
            "issue": "Many pending Windows updates",
            "severity": "medium",
            "evidence": f"{updates} hotfixes/updates detected",
            "fix": (
                "Run Windows Update (Settings → Windows Update → Check for updates). "
                "Pending updates can cause background scanning that slows the system."
            ),
            "top_offenders": [],
        }
    return None


def _rule_pending_updates_some(r: dict) -> dict | None:
    updates = r.get("os", {}).get("pending_updates")
    if updates is not None and 0 < updates <= 10:
        return {
            "issue": "Pending Windows updates",
            "severity": "low",
            "evidence": f"{updates} updates detected",
            "fix": (
                "Run Windows Update when convenient. "
                "Keeping Windows updated improves stability and security."
            ),
            "top_offenders": [],
        }
    return None


def _rule_uptime_very_long(r: dict) -> dict | None:
    uptime = r.get("os", {}).get("uptime_hours", 0)
    if uptime >= 168:  # 7 days
        return {
            "issue": "PC has not been restarted in over 7 days",
            "severity": "medium",
            "evidence": f"Uptime: {uptime} hours ({round(uptime / 24, 1)} days)",
            "fix": (
                "Restart your computer. Memory leaks and accumulated background "
                "tasks are cleared on restart, often restoring full speed."
            ),
            "top_offenders": [],
        }
    return None


def _rule_uptime_long(r: dict) -> dict | None:
    uptime = r.get("os", {}).get("uptime_hours", 0)
    if 72 <= uptime < 168:  # 3–7 days
        return {
            "issue": "PC has been running for several days without a restart",
            "severity": "low",
            "evidence": f"Uptime: {uptime} hours ({round(uptime / 24, 1)} days)",
            "fix": (
                "Consider restarting your PC soon. "
                "Regular restarts help clear memory and apply updates."
            ),
            "top_offenders": [],
        }
    return None


def _rule_disk_temp_cpu(r: dict) -> dict | None:
    temp = r.get("cpu", {}).get("temp_celsius")
    if temp is not None and temp > 85:
        return {
            "issue": "CPU temperature dangerously high",
            "severity": "high",
            "evidence": f"CPU temperature: {temp}°C",
            "fix": (
                "Immediately shut down and clean dust from your PC's vents and fans. "
                "Overheating causes throttling and can permanently damage hardware."
            ),
            "top_offenders": [],
        }
    return None


def _rule_cpu_temp_warm(r: dict) -> dict | None:
    temp = r.get("cpu", {}).get("temp_celsius")
    if temp is not None and 75 <= temp <= 85:
        return {
            "issue": "CPU running hot",
            "severity": "medium",
            "evidence": f"CPU temperature: {temp}°C",
            "fix": (
                "Clean dust from your PC vents. "
                "Make sure the fan is spinning and vents are not blocked."
            ),
            "top_offenders": [],
        }
    return None


# ---------------------------------------------------------------------------
# All rules in evaluation order (most impactful first within each severity)
# ---------------------------------------------------------------------------

_RULES = [
    _rule_ram_critical,
    _rule_cpu_critical,
    _rule_disk_space_critical,
    _rule_startup_critical,
    _rule_disk_temp_cpu,
    _rule_ram_high,
    _rule_cpu_high,
    _rule_disk_space_low,
    _rule_disk_type_hdd,
    _rule_startup_high,
    _rule_background_processes,
    _rule_pending_updates_many,
    _rule_uptime_very_long,
    _rule_cpu_temp_warm,
    _rule_pending_updates_some,
    _rule_uptime_long,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def diagnose(report: dict) -> list[dict]:
    """
    Run all rules against a collector JSON report.

    Args:
        report: The dict produced by collect.py (or any conforming JSON).

    Returns:
        List of issue dicts sorted by severity (high → medium → low).
        Returns an empty list for a healthy system.
    """
    issues = []
    for rule in _RULES:
        result = rule(report)
        if result is not None:
            issues.append(result)

    issues.sort(key=lambda x: _SEVERITY_ORDER.get(x["severity"], 99))
    return issues

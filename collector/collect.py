# -*- coding: utf-8 -*-
"""
PC Slowdown Diagnoser — Collector Script (Windows)
====================================================
Collects system telemetry and writes a single JSON report to disk.
No network calls. Run as a regular user; some fields (temp, updates)
require elevated privileges or compatible hardware and will be null if
unavailable — that is by design and does not affect other fields.

Usage:
    python collect.py                  # writes report.json in current dir
    python collect.py --out C:\\report.json

Output JSON schema: see sample_output.json
"""

import argparse
import json
import os
import platform
import sys
import time
import winreg
from datetime import datetime, timezone

import psutil

# Ensure stdout/stderr handle Unicode on Windows cmd (cp1252 → utf-8)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Optional WMI — graceful degradation if unavailable
# ---------------------------------------------------------------------------
try:
    import wmi as _wmi
    _WMI = _wmi.WMI()
except Exception:  # pragma: no cover
    _WMI = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _bytes_to_gb(n: int) -> float:
    return round(n / (1024 ** 3), 2)


def _safe(fn, default=None):
    """Call fn(), return default on any exception."""
    try:
        return fn()
    except Exception:
        return default


# ---------------------------------------------------------------------------
# CPU
# ---------------------------------------------------------------------------

def collect_cpu() -> dict:
    model = platform.processor() or "Unknown"

    # Warm up: first call returns 0.0 on Windows
    psutil.cpu_percent(interval=None)
    usage = psutil.cpu_percent(interval=1)

    temp = None
    if _WMI:
        temp = _safe(_get_cpu_temp)

    return {
        "model": model,
        "usage_percent": usage,
        "temp_celsius": temp,
    }


def _get_cpu_temp() -> float | None:
    """
    Try MSAcpi_ThermalZoneTemperature (requires admin + compatible driver).
    Returns degrees Celsius or None.
    """
    try:
        wmi_root = _wmi.WMI(namespace=r"root\wmi")
        zones = wmi_root.MSAcpi_ThermalZoneTemperature()
        if zones:
            # Convert from tenths of Kelvin → Celsius
            raw = zones[0].CurrentTemperature
            return round(raw / 10 - 273.15, 1)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# RAM
# ---------------------------------------------------------------------------

def collect_ram() -> dict:
    vm = psutil.virtual_memory()

    top_procs = []
    seen_pids = set()
    procs = []
    for p in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            info = p.info
            if info["memory_info"] and info["pid"] not in seen_pids:
                seen_pids.add(info["pid"])
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"] or "Unknown",
                    "ram_mb": round(info["memory_info"].rss / (1024 ** 2), 1),
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x["ram_mb"], reverse=True)
    top_procs = procs[:5]

    return {
        "total_gb": _bytes_to_gb(vm.total),
        "used_percent": vm.percent,
        "top_processes": top_procs,
    }


# ---------------------------------------------------------------------------
# Disk
# ---------------------------------------------------------------------------

def collect_disk() -> dict:
    usage = psutil.disk_usage("C:\\")
    free_percent = round(100 - usage.percent, 1)

    disk_type = _safe(_get_disk_type, default="Unknown")
    read_mbps, write_mbps = _safe(_get_disk_io_speed, default=(None, None))

    return {
        "free_percent": free_percent,
        "type": disk_type,
        "read_speed_mbps": read_mbps,
        "write_speed_mbps": write_mbps,
    }


def _get_disk_type() -> str:
    """Returns 'SSD', 'HDD', or 'Unknown' by querying WMI MediaType."""
    if not _WMI:
        return "Unknown"
    drives = _WMI.Win32_DiskDrive()
    if not drives:
        return "Unknown"
    media = str(drives[0].MediaType or "").lower()
    if "solid" in media or "ssd" in media:
        return "SSD"
    if "fixed" in media or "hard" in media or "hdd" in media:
        return "HDD"
    # Fallback: use WMI query for modern drives via MSFT_PhysicalDisk
    try:
        storage_wmi = _wmi.WMI(namespace=r"root\microsoft\windows\storage")
        physical_disks = storage_wmi.MSFT_PhysicalDisk()
        if physical_disks:
            media_type = physical_disks[0].MediaType
            # 3 = HDD, 4 = SSD
            if media_type == 4:
                return "SSD"
            if media_type == 3:
                return "HDD"
    except Exception:
        pass
    return "Unknown"


def _get_disk_io_speed() -> tuple[float, float]:
    """
    Returns (read_mbps, write_mbps) as a 1-second delta.
    This reflects current IO activity, not theoretical peak speed.
    """
    before = psutil.disk_io_counters()
    time.sleep(1)
    after = psutil.disk_io_counters()

    read_bytes = after.read_bytes - before.read_bytes
    write_bytes = after.write_bytes - before.write_bytes

    read_mbps = round(read_bytes / (1024 ** 2), 2)
    write_mbps = round(write_bytes / (1024 ** 2), 2)
    return read_mbps, write_mbps


# ---------------------------------------------------------------------------
# Startup programs
# ---------------------------------------------------------------------------

_STARTUP_KEYS = [
    (winreg.HKEY_LOCAL_MACHINE,
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_CURRENT_USER,
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
]


def collect_startup() -> dict:
    programs = []
    for hive, subkey in _STARTUP_KEYS:
        try:
            key = winreg.OpenKey(hive, subkey)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    programs.append({"name": name, "command": value})
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except OSError:
            continue

    # Deduplicate by name (case-insensitive)
    seen = set()
    unique = []
    for p in programs:
        key_name = p["name"].lower()
        if key_name not in seen:
            seen.add(key_name)
            unique.append(p)

    return {
        "count": len(unique),
        "programs": unique,
    }


# ---------------------------------------------------------------------------
# OS info
# ---------------------------------------------------------------------------

def collect_os() -> dict:
    version = platform.version()
    release = platform.release()
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    uptime_hours = round(uptime_seconds / 3600, 1)

    pending_updates = _safe(_get_pending_updates_count)

    return {
        "version": f"Windows {release} ({version})",
        "uptime_hours": uptime_hours,
        "pending_updates": pending_updates,
    }


def _get_pending_updates_count() -> int | None:
    """
    Best-effort count of installed (applied) hotfixes via WMI.
    This counts QFEs already applied, not pending ones — Windows Update
    pending-update APIs require UAC elevation and are very slow.
    Returns null on failure.
    """
    if not _WMI:
        return None
    fixes = _WMI.Win32_QuickFixEngineering()
    return len(fixes) if fixes is not None else None


# ---------------------------------------------------------------------------
# Background processes
# ---------------------------------------------------------------------------

def collect_background() -> dict:
    # Snapshot CPU usage over 1 second
    proc_list = []
    # First pass: start CPU measurement
    pids_started = {}
    for p in psutil.process_iter(["pid", "name"]):
        try:
            p.cpu_percent(interval=None)  # non-blocking first call
            pids_started[p.pid] = p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    time.sleep(1)

    for pid, p in pids_started.items():
        try:
            cpu = p.cpu_percent(interval=None)
            proc_list.append({
                "pid": pid,
                "name": p.name() or "Unknown",
                "cpu_percent": round(cpu, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    proc_list.sort(key=lambda x: x["cpu_percent"], reverse=True)

    return {
        "process_count": len(proc_list),
        "top_cpu_processes": proc_list[:5],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def collect_all() -> dict:
    print("[1/6] Collecting CPU info...")
    cpu = collect_cpu()

    print("[2/6] Collecting RAM info...")
    ram = collect_ram()

    print("[3/6] Collecting disk info (measuring IO speed over 1s)...")
    disk = collect_disk()

    print("[4/6] Collecting startup programs...")
    startup = collect_startup()

    print("[5/6] Collecting OS info...")
    os_info = collect_os()

    print("[6/6] Collecting background processes (sampling CPU over 1s)...")
    background = collect_background()

    report = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "startup": startup,
        "os": os_info,
        "background": background,
    }
    return report


def main():
    parser = argparse.ArgumentParser(
        description="PC Slowdown Diagnoser — System Collector"
    )
    parser.add_argument(
        "--out",
        default="report.json",
        help="Output JSON file path (default: report.json)",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("  PC Slowdown Diagnoser — Collecting system info")
    print("=" * 50)

    try:
        report = collect_all()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)

    out_path = os.path.abspath(args.out)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n[OK] Report written to: {out_path}")
    print(f"  Total processes: {report['background']['process_count']}")
    print(f"  RAM used:        {report['ram']['used_percent']}%")
    print(f"  Disk free:       {report['disk']['free_percent']}%")
    print(f"  Startup apps:    {report['startup']['count']}")
    print("=" * 50)


if __name__ == "__main__":
    main()

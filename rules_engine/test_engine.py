"""
Unit tests for the PC Slowdown Diagnoser Rules Engine.

Run with:
    python -m pytest test_engine.py -v
or:
    python test_engine.py
"""

import json
import os
import sys
import unittest

# Allow running from any working directory
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from engine import diagnose

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load(fixture_name: str) -> dict:
    path = os.path.join(_HERE, "fixtures", fixture_name)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _issues_by_severity(issues: list[dict], severity: str) -> list[dict]:
    return [i for i in issues if i["severity"] == severity]


def _issue_keys(issues: list[dict]) -> list[str]:
    return [i["issue"] for i in issues]


# ---------------------------------------------------------------------------
# Fixture: healthy machine
# ---------------------------------------------------------------------------

class TestHealthy(unittest.TestCase):

    def setUp(self):
        self.report = _load("healthy.json")
        self.issues = diagnose(self.report)

    def test_no_issues_produced(self):
        """A healthy machine must produce zero issues."""
        self.assertEqual(
            len(self.issues), 0,
            f"Expected 0 issues, got: {_issue_keys(self.issues)}"
        )

    def test_return_type_is_list(self):
        self.assertIsInstance(self.issues, list)


# ---------------------------------------------------------------------------
# Fixture: low RAM (93% used)
# ---------------------------------------------------------------------------

class TestLowRam(unittest.TestCase):

    def setUp(self):
        self.report = _load("low_ram.json")
        self.issues = diagnose(self.report)

    def test_has_issues(self):
        self.assertGreater(len(self.issues), 0)

    def test_ram_critical_issue_present(self):
        keys = _issue_keys(self.issues)
        self.assertIn("RAM critically full", keys)

    def test_ram_critical_is_high_severity(self):
        ram_issue = next(i for i in self.issues if i["issue"] == "RAM critically full")
        self.assertEqual(ram_issue["severity"], "high")

    def test_ram_issue_has_top_offenders(self):
        ram_issue = next(i for i in self.issues if i["issue"] == "RAM critically full")
        self.assertGreater(len(ram_issue["top_offenders"]), 0)
        self.assertIn("chrome.exe", ram_issue["top_offenders"])

    def test_ram_critical_not_also_ram_high(self):
        """Only one RAM rule should trigger — not both critical and high."""
        keys = _issue_keys(self.issues)
        self.assertNotIn("RAM usage high", keys)

    def test_sorted_high_first(self):
        """Issues must be sorted high → medium → low."""
        severities = [i["severity"] for i in self.issues]
        order = {"high": 0, "medium": 1, "low": 2}
        self.assertEqual(
            severities,
            sorted(severities, key=lambda s: order[s])
        )

    def test_pending_updates_low(self):
        """The fixture has 2 pending updates — should trigger low severity."""
        keys = _issue_keys(self.issues)
        self.assertIn("Pending Windows updates", keys)
        upd = next(i for i in self.issues if i["issue"] == "Pending Windows updates")
        self.assertEqual(upd["severity"], "low")


# ---------------------------------------------------------------------------
# Fixture: full disk (4.5% free, HDD)
# ---------------------------------------------------------------------------

class TestFullDisk(unittest.TestCase):

    def setUp(self):
        self.report = _load("full_disk.json")
        self.issues = diagnose(self.report)

    def test_disk_critical_present(self):
        keys = _issue_keys(self.issues)
        self.assertIn("Disk almost full", keys)

    def test_disk_critical_is_high(self):
        issue = next(i for i in self.issues if i["issue"] == "Disk almost full")
        self.assertEqual(issue["severity"], "high")

    def test_disk_space_low_not_also_triggered(self):
        """Only the more severe disk rule should fire."""
        keys = _issue_keys(self.issues)
        self.assertNotIn("Disk space low", keys)

    def test_hdd_type_issue_present(self):
        keys = _issue_keys(self.issues)
        self.assertIn("Using a slow hard drive (HDD)", keys)

    def test_hdd_issue_is_medium(self):
        issue = next(i for i in self.issues if i["issue"] == "Using a slow hard drive (HDD)")
        self.assertEqual(issue["severity"], "medium")

    def test_high_before_medium(self):
        """Disk critical (high) must come before HDD warning (medium)."""
        keys = _issue_keys(self.issues)
        disk_idx = keys.index("Disk almost full")
        hdd_idx = keys.index("Using a slow hard drive (HDD)")
        self.assertLess(disk_idx, hdd_idx)

    def test_issue_schema_complete(self):
        """Every issue must have all required keys."""
        required = {"issue", "severity", "evidence", "fix", "top_offenders"}
        for issue in self.issues:
            self.assertTrue(required.issubset(issue.keys()), f"Missing keys in: {issue}")


# ---------------------------------------------------------------------------
# Fixture: too many startup apps + long uptime + many updates
# ---------------------------------------------------------------------------

class TestTooManyStartup(unittest.TestCase):

    def setUp(self):
        self.report = _load("too_many_startup.json")
        self.issues = diagnose(self.report)

    def test_startup_critical_present(self):
        keys = _issue_keys(self.issues)
        self.assertIn("Too many startup programs", keys)

    def test_startup_critical_is_high(self):
        issue = next(i for i in self.issues if i["issue"] == "Too many startup programs")
        self.assertEqual(issue["severity"], "high")

    def test_startup_critical_has_offenders(self):
        issue = next(i for i in self.issues if i["issue"] == "Too many startup programs")
        self.assertGreaterEqual(len(issue["top_offenders"]), 5)

    def test_startup_high_not_also_triggered(self):
        keys = _issue_keys(self.issues)
        self.assertNotIn("Many startup programs", keys)

    def test_uptime_very_long_present(self):
        keys = _issue_keys(self.issues)
        self.assertIn("PC has not been restarted in over 7 days", keys)

    def test_uptime_long_not_also_triggered(self):
        """Only the more severe uptime rule should fire."""
        keys = _issue_keys(self.issues)
        self.assertNotIn("PC has been running for several days without a restart", keys)

    def test_many_pending_updates_present(self):
        keys = _issue_keys(self.issues)
        self.assertIn("Many pending Windows updates", keys)

    def test_background_processes_present(self):
        keys = _issue_keys(self.issues)
        self.assertIn("Excessive background processes", keys)

    def test_all_severities_valid(self):
        valid = {"high", "medium", "low"}
        for issue in self.issues:
            self.assertIn(issue["severity"], valid, f"Invalid severity in: {issue}")

    def test_top_offenders_is_list(self):
        for issue in self.issues:
            self.assertIsInstance(issue["top_offenders"], list)


# ---------------------------------------------------------------------------
# Edge-case / boundary tests
# ---------------------------------------------------------------------------

class TestBoundaryConditions(unittest.TestCase):

    def _make_report(self, **overrides) -> dict:
        """Build a minimal healthy report and apply field overrides."""
        base = {
            "cpu": {"model": "Test CPU", "usage_percent": 5.0, "temp_celsius": None},
            "ram": {"total_gb": 16.0, "used_percent": 30.0, "top_processes": []},
            "disk": {"free_percent": 60.0, "type": "SSD", "read_speed_mbps": 400.0, "write_speed_mbps": 300.0},
            "startup": {"count": 3, "programs": []},
            "os": {"version": "Windows 11", "uptime_hours": 2.0, "pending_updates": 0},
            "background": {"process_count": 80, "top_cpu_processes": []},
        }
        base.update(overrides)
        return base

    def test_exactly_90_ram_is_critical(self):
        r = self._make_report(ram={"total_gb": 16.0, "used_percent": 90.0, "top_processes": []})
        keys = _issue_keys(diagnose(r))
        self.assertIn("RAM critically full", keys)

    def test_89_ram_is_medium_not_critical(self):
        r = self._make_report(ram={"total_gb": 16.0, "used_percent": 89.0, "top_processes": []})
        keys = _issue_keys(diagnose(r))
        self.assertNotIn("RAM critically full", keys)
        self.assertIn("RAM usage high", keys)

    def test_exactly_10_disk_free_is_not_critical(self):
        r = self._make_report(disk={"free_percent": 10.0, "type": "SSD", "read_speed_mbps": 400.0, "write_speed_mbps": 300.0})
        keys = _issue_keys(diagnose(r))
        self.assertNotIn("Disk almost full", keys)
        self.assertIn("Disk space low", keys)

    def test_9_9_disk_free_is_critical(self):
        r = self._make_report(disk={"free_percent": 9.9, "type": "SSD", "read_speed_mbps": 400.0, "write_speed_mbps": 300.0})
        keys = _issue_keys(diagnose(r))
        self.assertIn("Disk almost full", keys)

    def test_null_pending_updates_does_not_crash(self):
        r = self._make_report(os={"version": "Windows 11", "uptime_hours": 5.0, "pending_updates": None})
        issues = diagnose(r)
        self.assertIsInstance(issues, list)

    def test_null_cpu_temp_does_not_crash(self):
        r = self._make_report(cpu={"model": "Test", "usage_percent": 5.0, "temp_celsius": None})
        issues = diagnose(r)
        self.assertIsInstance(issues, list)

    def test_empty_report_does_not_crash(self):
        issues = diagnose({})
        self.assertIsInstance(issues, list)

    def test_exactly_168h_uptime_is_very_long(self):
        r = self._make_report(os={"version": "Windows 11", "uptime_hours": 168.0, "pending_updates": 0})
        keys = _issue_keys(diagnose(r))
        self.assertIn("PC has not been restarted in over 7 days", keys)

    def test_cpu_temp_86_is_dangerous(self):
        r = self._make_report(cpu={"model": "Test", "usage_percent": 5.0, "temp_celsius": 86.0})
        issues = diagnose(r)
        keys = _issue_keys(issues)
        self.assertIn("CPU temperature dangerously high", keys)
        issue = next(i for i in issues if i["issue"] == "CPU temperature dangerously high")
        self.assertEqual(issue["severity"], "high")


# ---------------------------------------------------------------------------
# Run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)

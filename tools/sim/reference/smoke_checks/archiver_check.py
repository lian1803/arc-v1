"""archiver_check.py — archiver.py error-path regression (check 3).

Isolated from live_and_spawn because it mutates disk (creates/deletes a real
archived file); easier to reason about and reorder without touching the
purely-read runtime probes.
"""
from __future__ import annotations

import time

from ._core import CheckResult


def check_3_archiver_paths() -> CheckResult:
    name = "archiver.py error paths"
    try:
        from parts._shared.archiver import archive_research_output
    except Exception as e:
        return CheckResult(3, name, "FAIL", "BLOCKER", f"import failed: {e}", "check archiver.py")
    ev: list[str] = []
    try:
        archive_research_output("", "smoke_empty", "smoke")
        return CheckResult(3, name, "FAIL", "BLOCKER",
            "empty content did NOT raise ValueError",
            "restore DOCTRINE §2 guard in archiver")
    except ValueError:
        ev.append("empty -> ValueError OK")
    brief = f"zzsmoke_{int(time.time() * 1000)}"
    try:
        p = archive_research_output("# smoke\n", brief, "smoke_agent")
        ev.append(f"happy -> {p.name}")
        try:
            archive_research_output("# dup\n", brief, "smoke_agent")
            return CheckResult(3, name, "FAIL", "BLOCKER",
                "duplicate did NOT raise FileExistsError", "restore collision guard")
        except FileExistsError:
            ev.append("dup -> FileExistsError OK")
        finally:
            try:
                p.unlink()
                if not any(p.parent.iterdir()):
                    p.parent.rmdir()
            except OSError:
                pass
    except Exception as e:
        return CheckResult(3, name, "FAIL", "BLOCKER", f"happy-path raised: {e}", "archiver broken")
    return CheckResult(3, name, "PASS", None, "; ".join(ev))

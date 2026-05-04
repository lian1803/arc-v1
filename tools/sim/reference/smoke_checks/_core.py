"""_core.py — shared types + filesystem helpers for smoke_checks children.

Lives here (not __init__.py) so sibling modules can import without triggering
the full package eager-load chain.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

ARC_ROOT = Path(__file__).resolve().parents[2]
COST_LOG = ARC_ROOT / "shared" / "knowledge" / "cost_log.jsonl"

if str(ARC_ROOT) not in sys.path:
    sys.path.insert(0, str(ARC_ROOT))

Status = Literal["PASS", "FAIL", "SKIP"]
Severity = Literal["BLOCKER", "WARN", "INFO"]


@dataclass
class CheckResult:
    id: int
    name: str
    status: Status
    severity: Optional[Severity] = None
    evidence: str = ""
    fix: Optional[str] = None


def _count_log_lines() -> int:
    if not COST_LOG.exists():
        return 0
    with open(COST_LOG, "r", encoding="utf-8") as f:
        return sum(1 for _ in f if _.strip())


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

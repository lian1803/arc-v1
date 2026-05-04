"""smoke_checks package — split from tools/smoke_checks.py per DOCTRINE §9.

Children:
  _core.py          — CheckResult dataclass + filesystem helpers
  live_and_spawn.py — checks 1, 2, 4 (runtime/behavior)
  archiver_check.py — check 3 (archiver error paths; mutates disk)
  indices.py        — checks 5, 6, 7 (INDEX/import-graph integrity)
  state.py          — checks 8, 9, 10, 11 (static repo-state invariants)
"""

from ._core import CheckResult
from .live_and_spawn import check_1_tools_live, check_2_spawn_assembly, check_4_hooks_smoke
from .archiver_check import check_3_archiver_paths
from .indices import check_5_knowledge_index, check_6_doctrine_imports, check_7_decisions_index
from .state import (
    check_8_pending_done,
    check_9_spec_phase,
    check_10_size_caps,
    check_11_cross_refs,
)

__all__ = [
    "CheckResult",
    "check_1_tools_live",
    "check_2_spawn_assembly",
    "check_3_archiver_paths",
    "check_4_hooks_smoke",
    "check_5_knowledge_index",
    "check_6_doctrine_imports",
    "check_7_decisions_index",
    "check_8_pending_done",
    "check_9_spec_phase",
    "check_10_size_caps",
    "check_11_cross_refs",
]

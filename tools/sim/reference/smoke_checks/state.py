"""state.py — repo-state invariants (checks 8, 9, 10, 11).

Grouped because all four are pure static reads of top-level ARC docs
(PENDING/DONE, SPEC phase, size caps, @-import cross-refs). No subprocess,
no mutation — fastest checks, safe to batch.
"""
from __future__ import annotations

import re
from pathlib import Path

from ._core import ARC_ROOT, COST_LOG, CheckResult, _read


def check_8_pending_done() -> CheckResult:
    name = "PENDING vs DONE"
    pending = _read(ARC_ROOT / "PENDING.md")
    done = _read(ARC_ROOT / "DONE.md")
    p_items = set(re.findall(r'^\s*-\s*\[[ x]\]\s*(.+?)$', pending, re.MULTILINE))
    d_items = set(re.findall(r'^\s*-\s*\[x\]\s*(.+?)$', done, re.MULTILINE))
    dupes = {x for x in (p_items & d_items) if "[legacy]" not in x.lower()}
    if dupes:
        return CheckResult(8, name, "FAIL", "WARN",
            f"{len(dupes)} dupe(s): " + "; ".join(list(dupes)[:3]),
            "move or tag [legacy]")
    return CheckResult(8, name, "PASS", None,
        f"{len(p_items)} pending / {len(d_items)} done; no untagged dupes")


def check_9_spec_phase() -> CheckResult:
    name = "SPEC §5 phase alignment"
    spec = _read(ARC_ROOT / "SPEC.md")
    m = re.search(r'\*\*Current:\s*Phase\s*(\d)\s*gate', spec)
    if not m:
        return CheckResult(9, name, "FAIL", "WARN",
            "SPEC.md §5 'Current:' line not found", "restore current-phase line")
    phase = int(m.group(1))
    if phase == 3:
        proof = COST_LOG.exists() and (ARC_ROOT / "tools" / "search.py").exists()
        if not proof:
            return CheckResult(9, name, "FAIL", "BLOCKER",
                "Phase 3 claim but tools/cost_log missing",
                "restore evidence or revert phase")
    return CheckResult(9, name, "PASS", None, f"Phase {phase} gate; exit evidence on disk")


def check_10_size_caps() -> CheckResult:
    name = "file-size caps"
    bad: list[str] = []
    excl = ("shared/message_pool/", "shared/knowledge/research_outputs/", "자료들/")

    def skip(p: Path) -> bool:
        rel = p.relative_to(ARC_ROOT).as_posix()
        return any(rel.startswith(x) for x in excl)

    for p in ARC_ROOT.glob("**/*.md"):
        if skip(p):
            continue
        n = len(_read(p).splitlines())
        rel = p.relative_to(ARC_ROOT).as_posix()
        if "parts/" in rel and "/agents/" in rel and n > 150:
            bad.append(f"{rel}: {n} LOC (cap 150)")
        elif p.name != "DOCTRINE.md" and n > 200:
            bad.append(f"{rel}: {n} LOC (cap 200)")
    for p in ARC_ROOT.glob("**/*.py"):
        if skip(p):
            continue
        n = len(_read(p).splitlines())
        if n > 300:
            bad.append(f"{p.relative_to(ARC_ROOT).as_posix()}: {n} LOC (cap 300)")
    if bad:
        return CheckResult(10, name, "FAIL", "WARN",
            f"{len(bad)} over-cap:\n- " + "\n- ".join(bad[:5]),
            "split per DOCTRINE §9")
    return CheckResult(10, name, "PASS", None, "all files under cap")


def check_11_cross_refs() -> CheckResult:
    name = "session cross-doc refs"
    targets = [ARC_ROOT / "parts" / "planning" / "CLAUDE.md",
        ARC_ROOT / "SPEC.md", ARC_ROOT / "CLAUDE.md"]
    missing: list[str] = []
    for t in targets:
        if not t.exists():
            continue
        # v2: tighten @-import matcher. Anchor to bullet-start, capture exact
        # path ending in `.md` at a word boundary (whitespace/EOL/em-dash), so
        # `- @X.md — desc` matches while inline prose `@X.md` does not.
        for rel in re.findall(r'^\s*-\s*@(\S+\.md)(?=\s|$)', _read(t), re.MULTILINE):
            if not (t.parent / rel).resolve().exists():
                missing.append(f"{t.name} -> @{rel}")
    if missing:
        return CheckResult(11, name, "FAIL", "WARN",
            f"{len(missing)} broken @-ref(s):\n- " + "\n- ".join(missing[:5]),
            "fix @-ref or create target")
    return CheckResult(11, name, "PASS", None, "all sampled @-imports resolve")

"""indices.py — registry/INDEX integrity (checks 5, 6, 7).

Grouped because all three verify that a declarative index/import graph
(knowledge INDEX.md, agent-file import chain, decisions INDEX.md) matches
what is actually on disk. Drift here = §6 Accumulate-Never-Delete violation.
"""
from __future__ import annotations

import random
import re

from ._core import ARC_ROOT, CheckResult, _read


def check_5_knowledge_index() -> CheckResult:
    name = "knowledge INDEX resolution"
    idx = ARC_ROOT / "shared" / "knowledge" / "INDEX.md"
    if not idx.exists():
        return CheckResult(5, name, "FAIL", "BLOCKER", f"missing {idx}", "create INDEX.md")
    text = _read(idx)
    refs = [r for r in re.findall(r'\]\(([^)]+\.md)\)', text) if not r.startswith("http")]
    missing = [r for r in refs if not (idx.parent / r).resolve().exists()]
    if missing:
        return CheckResult(5, name, "FAIL", "BLOCKER",
            f"{len(missing)}/{len(refs)} refs missing: " + ", ".join(missing[:5]),
            "update INDEX.md or add file")
    # v2: tighten source URL extraction — require single-space after `source:`
    # and terminate on clean delimiters only (whitespace, `;`, `)`) to avoid
    # bracket/inline-comment miscapture. Format is inline `(source: https://...; ...)`.
    urls = re.findall(r'source:\s+(https?://[^\s;)]+)', text)
    sample = random.sample(urls, min(3, len(urls))) if urls else []
    bad = [u for u in sample if not re.match(r'^https?://[^\s]+$', u)]
    if bad:
        return CheckResult(5, name, "FAIL", "WARN", f"{len(bad)} malformed URL(s): {bad}",
            "fix frontmatter source URL")
    return CheckResult(5, name, "PASS", None,
        f"{len(refs)} refs resolved; {len(sample)} URLs sampled")


def _is_non_dispatchable_md(path) -> bool:
    """Mirrors live_and_spawn._is_non_dispatchable. Skip reference modules,
    split children, index files. Session 19 expanded heuristic."""
    if path.name.endswith("_INDEX.md") or path.name == "INDEX.md":
        return True
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    if "\n- @" not in text and "\n-@" not in text:
        return True
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False
    fm = text[3:end]
    non_dispatch_type_values = (
        "index", "module", "subspec", "reference", "navigation", "spec",
    )
    for line in fm.splitlines():
        s = line.strip()
        if s.startswith("parent:") and s not in ("parent:", "parent: null"):
            return True
        for prefix in ("type:", "kind:"):
            if s.startswith(prefix):
                val = s[len(prefix):].strip().strip('"').strip("'").lower()
                if val in non_dispatch_type_values:
                    return True
        if s.startswith("role:"):
            val = s[5:].strip().lower()
            if any(val.startswith(x) for x in (
                "navigation", "index-only", "reference module",
                "index", "module ", "subspec",
            )):
                return True
    return False


_is_split_child_md = _is_non_dispatchable_md


def check_6_doctrine_imports() -> CheckResult:
    name = "DOCTRINE import chain"
    required = {"DOCTRINE.md", "constitution.md", "rubric.md", "verifier.md"}
    all_agents = list((ARC_ROOT / "parts").glob("*/agents/*.md"))
    agents = [a for a in all_agents if not _is_non_dispatchable_md(a)]
    skipped = len(all_agents) - len(agents)
    missing: list[str] = []
    for a in agents:
        txt = _read(a)
        have = {n for n in required if n in txt}
        if have != required:
            missing.append(f"{a.relative_to(ARC_ROOT)} lacks {sorted(required - have)}")
    if missing:
        return CheckResult(6, name, "FAIL", "BLOCKER",
            f"{len(missing)}/{len(agents)} agents missing:\n- " + "\n- ".join(missing[:5]),
            "add @imports per agent_template.md")
    return CheckResult(6, name, "PASS", None,
        f"{len(agents)} agents reference all 4 mandatory imports ({skipped} split-children skipped)")


def check_7_decisions_index() -> CheckResult:
    name = "decisions/INDEX consistency"
    idx = ARC_ROOT / "decisions" / "INDEX.md"
    on_disk = {p.name for p in (ARC_ROOT / "decisions").glob("*.md")
        if p.name not in {"INDEX.md", "README.md", "constitution.md"}}
    # v2: scope parsing to the 5 official sections only. `## How to Add an Entry`
    # contains a `YYYY-MM-DD_topic.md` template literal that would false-positive.
    body = _read(idx)
    m = re.search(r'(?ms)^## Planning\b.*?(?=^## How to Add|\Z)', body)
    scoped = m.group(0) if m else body
    listed = set(re.findall(r'\]\(\./([^)]+\.md)\)', scoped))
    disk_only, idx_only = on_disk - listed, listed - on_disk
    if disk_only or idx_only:
        msg: list[str] = []
        if disk_only:
            msg.append(f"on-disk not listed: {sorted(disk_only)[:5]}")
        if idx_only:
            msg.append(f"listed not on-disk: {sorted(idx_only)[:5]}")
        return CheckResult(7, name, "FAIL", "WARN", "; ".join(msg),
            "reconcile INDEX with disk")
    return CheckResult(7, name, "PASS", None, f"{len(on_disk)} files match INDEX entries")

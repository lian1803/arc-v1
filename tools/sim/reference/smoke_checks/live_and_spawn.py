"""live_and_spawn.py — infrastructure/behavior checks (1, 2, 4).

Groups live tools call + agent-assembly + hook disk presence. All three
probe runtime/behavior surfaces rather than static file content.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from ._core import ARC_ROOT, CheckResult, _count_log_lines, _read


def check_1_tools_live(live: bool) -> CheckResult:
    name = "tools live-call"
    if not live:
        return CheckResult(1, name, "SKIP", "INFO",
            "--live not set (budget protection, $0.006/run)",
            "re-run with --live when regressing tools edit")
    before = _count_log_lines()
    try:
        r1 = subprocess.run([sys.executable, str(ARC_ROOT / "tools" / "search.py"),
            "ARC smoke test ping"], capture_output=True, text=True, timeout=30)
        r2 = subprocess.run([sys.executable, str(ARC_ROOT / "tools" / "browse.py"),
            "https://example.com"], capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired as e:
        return CheckResult(1, name, "FAIL", "BLOCKER", f"timeout: {e}", "check network / API keys")
    after = _count_log_lines()
    if r1.returncode != 0 or r2.returncode != 0:
        return CheckResult(1, name, "FAIL", "BLOCKER",
            f"search rc={r1.returncode} browse rc={r2.returncode}; "
            f"search_err={r1.stderr[:150]} browse_err={r2.stderr[:150]}",
            "inspect tools/*.py; likely API key / network")
    if after - before < 2:
        return CheckResult(1, name, "FAIL", "BLOCKER",
            f"cost_log grew by {after - before}, expected >=2",
            "tools/*.py log_call() not firing")
    return CheckResult(1, name, "PASS", None, f"cost_log grew {before} -> {after} (>=2 entries)")


def _is_non_dispatchable(path) -> bool:
    """Skip files that are reference modules, split children, or indexes.
    These are not independently dispatchable via spawn.py; they inherit @imports
    from their dispatchable parent or aren't dispatched at all.

    Detection (session 19 expanded heuristic):
    - filename ends `_INDEX.md` or equals `INDEX.md`
    - frontmatter has `parent: X` (split child)
    - frontmatter `type:` / `kind:` is one of: index, module, subspec,
      reference, navigation, spec
    - frontmatter `role:` starts with Navigation|Index-only|Reference module
    - file has zero `@import` style references (empty-import reference doc)

    A real dispatchable agent always has at least one `- @...` import per
    agent_template.md contract. The all-four-mandatory check still catches
    mis-authored dispatchable agents (they'll have *some* imports but miss
    one of the four)."""
    if path.name.endswith("_INDEX.md") or path.name == "INDEX.md":
        return True
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    # Zero @imports = reference doc, not dispatchable.
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


_is_split_child = _is_non_dispatchable


def check_2_spawn_assembly() -> CheckResult:
    name = "spawn.py assembly"
    try:
        from parts._shared.spawn import assemble
    except Exception as e:
        return CheckResult(2, name, "FAIL", "BLOCKER", f"import failed: {e}", "check spawn.py")
    failures: list[str] = []
    tried = 0
    skipped = 0
    for agent_md in (ARC_ROOT / "parts").glob("*/agents/*.md"):
        if _is_non_dispatchable(agent_md):
            skipped += 1
            continue
        tried += 1
        try:
            assemble(agent_md, brief=None)
        except Exception as e:
            failures.append(f"{agent_md.relative_to(ARC_ROOT)}: {e}")
    if failures:
        return CheckResult(2, name, "FAIL", "BLOCKER",
            f"{len(failures)}/{tried} agents failed:\n- " + "\n- ".join(failures[:5]),
            "fix missing @imports per agent_template.md")
    return CheckResult(2, name, "PASS", None,
        f"{tried} agents assembled cleanly ({skipped} split-children skipped)")


def check_4_hooks_smoke() -> CheckResult:
    name = "hook smoke"
    settings = ARC_ROOT / ".claude" / "settings.json"
    if not settings.exists():
        return CheckResult(4, name, "FAIL", "BLOCKER", f"missing {settings}", "reinstall hooks")
    cfg = json.loads(_read(settings))
    declared: list[Path] = []
    for _evt, entries in cfg.get("hooks", {}).items():
        for group in entries:
            for h in group.get("hooks", []):
                m = re.search(r'"([^"]+\.(?:sh|py))"', h.get("command", ""))
                if m:
                    declared.append(Path(m.group(1)))
    missing = [p for p in declared if not p.exists()]
    if missing:
        return CheckResult(4, name, "FAIL", "BLOCKER",
            f"{len(missing)} hook(s) missing: " + ", ".join(p.name for p in missing[:5]),
            "restore hook script or fix settings.json")
    return CheckResult(4, name, "SKIP", "INFO",
        f"{len(declared)} hook scripts on disk; live stdin-mock requires harness context",
        "invoke via real Claude Code events for full smoke")

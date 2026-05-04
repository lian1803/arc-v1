#!/usr/bin/env python3
"""ARC 루트 cap 가드.

PreToolUse(Write|Edit) 발동. ARC 루트 화이트리스트 외 신규 파일 = exit 2 차단.
- 기존 파일 Edit는 허용 (경로 검사만 통과).
- `.tmp_*`/`temp_*`/`scratch_*` 는 archive/scratch/YYYY-MM/ 권고.

룰 출처: .claude/rules/file-routing.md
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

try:
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

WHITELIST_FILES = {
    "CLAUDE.md",
    "AGENTS.md",
    ".env",
    ".env.example",
    ".gitignore",
    ".cost_log.jsonl",
}

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HOOK_DIR, "..", ".."))


def main() -> int:
    try:
        ev = json.loads(sys.stdin.read())
    except Exception:
        return 0

    if ev.get("tool_name") not in {"Write", "Edit"}:
        return 0

    path = (ev.get("tool_input") or {}).get("file_path", "")
    if not path:
        return 0

    abs_p = os.path.normpath(os.path.abspath(path))

    if os.path.dirname(abs_p) != ROOT:
        return 0

    name = os.path.basename(abs_p)

    if name in WHITELIST_FILES:
        return 0

    if os.path.exists(abs_p):
        return 0

    ym = datetime.now().strftime("%Y-%m")
    if name.startswith((".tmp_", "temp_", "scratch_")):
        suggest = f"archive/scratch/{ym}/{name}"
        msg = (
            f"[ARC route-guard] 루트 cap: '{name}' 차단. "
            f"임시 파일은 '{suggest}' 으로 보내라."
        )
    else:
        msg = (
            f"[ARC route-guard] 루트 cap: '{name}' 차단. "
            f"ARC 루트는 화이트리스트만. 패턴별 라우팅 → .claude/rules/file-routing.md. "
            f"진짜 루트가 맞으면 화이트리스트 갱신 + Lian 동의."
        )
    print(msg, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

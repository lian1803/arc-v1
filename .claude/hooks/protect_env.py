#!/usr/bin/env python3
# PreToolUse: 운영 사고 차단.
# 막는 것: .env shell-edit / destructive git / rm -rf / curl|bash / .env Write.
# 허용: .env Read+Edit / 일반 Bash / 일반 Write,Edit.
# 메모리 사고 직격: feedback_env_shell_edits_forbidden, feedback_subagent_commit_drift.

import json, re, sys

try:
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "")
inp = data.get("tool_input") or {}


def block(reason):
    print(f"BLOCKED: {reason}", file=sys.stderr)
    sys.exit(2)


if tool == "Bash":
    cmd = inp.get("command", "") or ""

    if re.search(r">>?\s*[\w./-]*\.env\b", cmd):
        block(".env 에 redirect 금지. Read+Edit 만 허용. (memory: feedback_env_shell_edits_forbidden, .env 손상 3건)")
    if re.search(r"\bsed\s+-i\b", cmd) and re.search(r"\.env\b", cmd):
        block("sed -i 로 .env 수정 금지. Read+Edit 만 허용.")

    if re.search(r"\bgit\s+push\b.*--force", cmd) and re.search(r"\b(main|master)\b", cmd):
        block("force push to main/master 금지.")
    if re.search(r"\bgit\s+reset\s+--hard\b", cmd):
        block("git reset --hard 금지. 안전한 alternative 사용.")
    if re.search(r"\bgit\s+checkout\s+--\s+\.\s*$", cmd):
        block("git checkout -- . (전체 discard) 금지.")
    if re.search(r"\bgit\s+clean\s+-[a-zA-Z]*f", cmd):
        block("git clean -f 금지. untracked 검토 먼저.")

    if re.search(r"\brm\s+(-[rRf]+\s+)+(/|~|\$HOME|\.\s|\.$)", cmd):
        block("rm -rf on root/home/. 금지.")

    if re.search(r"\b(curl|wget)\b.+\|\s*(bash|sh|zsh)\b", cmd):
        block("curl|bash 금지. 다운로드 후 검토.")

    if re.search(r"\bchmod\s+(-R\s+)?(0?777|a\+rwx)\b", cmd):
        block("chmod 777 금지.")

if tool == "Write":
    path = (inp.get("file_path") or "").replace("\\", "/")
    if path.endswith("/.env") or path == ".env" or path.endswith("/.env.local") or path.endswith("/.env.production"):
        block(".env 는 Write 금지. Read+Edit 만. (memory: feedback_env_shell_edits_forbidden)")

sys.exit(0)

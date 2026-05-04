#!/usr/bin/env python3
# Stop hook: 산출물 self-verify reminder.
# 매 Stop 마다 stderr 로 reminder 1줄. block X (무한루프 방지).
# 메모리 직격: feedback_self_verify_before_handoff, feedback_outbound_artifact_e2e.

import json, sys

try:
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if data.get("stop_hook_active"):
    sys.exit(0)

print(
    "[verify_done] 산출물 self-verify 했나? "
    "outbound (image / PDF / CSV / HTML / 카드 / 메타) = read/play/parse 직접 확인 의무. "
    "sub-agent OK 보고 ≠ self-verify. "
    "(memory: feedback_self_verify_before_handoff)",
    file=sys.stderr,
)
sys.exit(0)

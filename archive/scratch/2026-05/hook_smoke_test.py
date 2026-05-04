"""hook 스모크 테스트 — 5케이스. 일회용, archive/scratch에 두는 게 룰 정합."""
import json
import subprocess
import sys

HOOK = r"D:\work\ARC\.claude\hooks\route_root_writes.py"

CASES = [
    # (label, tool, path, expected_exit)
    (".tmp_test.py 신규 (차단)", "Write", r"D:\work\ARC\.tmp_test.py", 2),
    ("foo.py 루트 신규 (차단)", "Write", r"D:\work\ARC\foo.py", 2),
    ("NEXT.md 루트 신규 (차단 — 이미 .claude/docs/로 이동)", "Write", r"D:\work\ARC\NEXT.md", 2),
    ("MODES.md 루트 신규 (차단)", "Write", r"D:\work\ARC\MODES.md", 2),
    ("CLAUDE.md Edit (통과)", "Edit", r"D:\work\ARC\CLAUDE.md", 0),
    (".claude/docs/NEXT.md Edit (통과)", "Edit", r"D:\work\ARC\.claude\docs\NEXT.md", 0),
    ("tools/new.py 신규 (통과)", "Write", r"D:\work\ARC\tools\new.py", 0),
    ("archive/scratch/.tmp_x.py (통과)", "Write", r"D:\work\ARC\archive\scratch\2026-05\.tmp_x.py", 0),
    ("Bash (통과 — Write/Edit 아님)", "Bash", r"D:\work\ARC\.tmp_x.py", 0),
]

ok = True
for label, tool, path, want in CASES:
    ev = {"tool_name": tool, "tool_input": {"file_path": path}}
    r = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(ev),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    mark = "OK" if r.returncode == want else "FAIL"
    if r.returncode != want:
        ok = False
    print(f"[{mark}] {label}  exit={r.returncode} (want {want})")
    if r.stderr.strip():
        print(f"        stderr: {r.stderr.strip()}")

print()
print("ALL OK" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)

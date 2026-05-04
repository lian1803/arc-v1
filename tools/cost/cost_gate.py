#!/usr/bin/env python
"""cost_gate.py — session 13 patch #5

Read shared/knowledge/cost_log.jsonl, sum recent spend, compare against caps.
Blocks downstream tool/agent spawn if over cap.

Usage:
    python tools/cost_gate.py [--session SESSION_ID] [--window-hours 24] [--json]

Caps (default, configurable via shared/config.json):
    session_cap_usd: 5.0
    daily_cap_usd: 20.0
    monthly_cap_usd: 200.0

Exit codes:
    0 — under all caps
    2 — any cap exceeded (blocks downstream spawn)
    1 — config / file read error (DOCTRINE §2)

Integration:
    - spawn.py pre-spawn check (session 14+ proposed).
    - DOCTRINE §11 staged addition: "spawn 전 cost_gate 필수" (Lian 사인 대기).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
COST_LOG = ROOT / ".cost_log.jsonl"
CONFIG = ROOT / ".cost_config.json"  # optional, DEFAULT_CAPS used if missing

DEFAULT_CAPS = {
    "session_cap_usd": 5.0,
    "daily_cap_usd": 20.0,
    "monthly_cap_usd": 200.0,
}


def load_caps() -> dict[str, float]:
    if not CONFIG.exists():
        return dict(DEFAULT_CAPS)
    try:
        raw = json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: config.json unreadable: {e}", file=sys.stderr)
        raise SystemExit(1)
    caps = raw.get("cost_caps_usd", {})
    return {**DEFAULT_CAPS, **{k: float(v) for k, v in caps.items()}}


def load_entries() -> list[dict[str, Any]]:
    if not COST_LOG.exists():
        return []
    entries = []
    for line in COST_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            # DOCTRINE §2: surface corruption, don't swallow
            print(f"WARN: cost_log corruption at line: {line[:80]}", file=sys.stderr)
    return entries


def sum_window(entries: list[dict], since: datetime, session_id: str | None = None) -> float:
    total = 0.0
    for e in entries:
        ts_raw = e.get("timestamp") or e.get("ts")
        if not ts_raw:
            continue
        try:
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if ts < since:
            continue
        if session_id and e.get("session_id") != session_id:
            continue
        cost = e.get("cost_usd", e.get("cost", 0.0))
        try:
            total += float(cost)
        except (TypeError, ValueError):
            continue
    return total


def main() -> int:
    p = argparse.ArgumentParser(description="ARC cost gate — blocks if over cap.")
    p.add_argument("--session", default=None, help="Session ID for session-cap check.")
    p.add_argument("--window-hours", type=int, default=24, help="Hours for daily-cap window.")
    p.add_argument("--json", action="store_true", help="JSON output.")
    args = p.parse_args()

    caps = load_caps()
    entries = load_entries()

    now = datetime.now(timezone.utc)
    daily_since = now - timedelta(hours=args.window_hours)
    monthly_since = now - timedelta(days=30)
    session_since = now - timedelta(hours=12)  # session horizon

    daily = sum_window(entries, daily_since)
    monthly = sum_window(entries, monthly_since)
    session = sum_window(entries, session_since, session_id=args.session) if args.session else 0.0

    status: dict[str, Any] = {
        "session_usd": session,
        "session_cap": caps["session_cap_usd"],
        "session_over": session > caps["session_cap_usd"],
        "daily_usd": daily,
        "daily_cap": caps["daily_cap_usd"],
        "daily_over": daily > caps["daily_cap_usd"],
        "monthly_usd": monthly,
        "monthly_cap": caps["monthly_cap_usd"],
        "monthly_over": monthly > caps["monthly_cap_usd"],
    }
    status["blocked"] = any(status[k] for k in ("session_over", "daily_over", "monthly_over"))

    if args.json:
        print(json.dumps(status, ensure_ascii=False))
    else:
        print(f"cost_gate: session=${session:.4f}/${caps['session_cap_usd']:.2f} "
              f"daily=${daily:.4f}/${caps['daily_cap_usd']:.2f} "
              f"monthly=${monthly:.4f}/${caps['monthly_cap_usd']:.2f} "
              f"{'BLOCKED' if status['blocked'] else 'OK'}")

    return 2 if status["blocked"] else 0


if __name__ == "__main__":
    sys.exit(main())

"""Append-only JSONL cost logger for ARC tool calls.

Writes one line per tool invocation to `shared/knowledge/cost_log.jsonl`.

Contract (DOCTRINE §2 No-Silent-Fail):
- Any file-system or JSON-encode failure RAISES. Callers decide whether the
  upstream work is still valid without the log entry. We never pretend to
  have logged.

Design pattern reuse (see shared/message_pool/strategy/20260421_phase2-tools/design.md):
- JSONL shape + atomic-ish append: core/company/utils/monitor.py
- Path discovery: parts/_shared/spawn.py (walks up to ARC root)

COSTS union schema (added 2026-04-21 P0-9):
- "per_request" entries: flat USD per call (Perplexity, browse). Token args ignored.
- "per_mtok" entries: USD per million input/output tokens (Anthropic / OpenAI /
  Gemini). Caller MUST pass input_tokens + output_tokens for accurate cost;
  omitting both raises (DOCTRINE §2, no silent 0-cost).
All prices live-fetched 2026-04-21 from the provider's official pricing page;
URL + access-date cited inline next to each entry.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Resolve ARC root (tools/cost/cost_log.py → 2 levels up).
# luna had shared/knowledge/cost_log.jsonl; ARC keeps it as a hidden root file
# (no shared/ folder per ARC minimalism).
ARC_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ARC_ROOT / ".cost_log.jsonl"

# Cost table — union schema. Access-date 2026-04-21 on every entry.
# When a provider changes pricing, bump the constant AND append a decisions/ entry.
COSTS = {
    # Perplexity — per-request simplified (low-context baseline).
    # https://docs.perplexity.ai/guides/pricing  (access 2026-04-21)
    # Live page: sonar-pro $6-14 / 1000 req; sonar $5-12 / 1000 req. We log the
    # low-context rate; callers on higher context tiers pass metadata.context.
    "perplexity:sonar-pro": {"unit": "per_request", "usd": 0.006},
    "perplexity:sonar":     {"unit": "per_request", "usd": 0.005},
    "browse:http":          {"unit": "per_request", "usd": 0.000},  # no API cost; trace only

    # YouTube — yt-dlp = no API cost (DOCTRINE §0 ToS gray, info-only surface).
    # Data API v3 = free under 10K quota/day; search costs 100 unit/req. Logged as 0 for now.
    "youtube:ytdlp_fallback": {"unit": "per_request", "usd": 0.000},
    "youtube:data_api":       {"unit": "per_request", "usd": 0.000},
    "yt_dlp":                 {"unit": "per_request", "usd": 0.000},

    # Anthropic — https://claude.com/pricing  (access 2026-04-21)
    "anthropic:opus-4.7":   {"unit": "per_mtok", "in_usd":  5.00, "out_usd": 25.00},
    "anthropic:sonnet-4.6": {"unit": "per_mtok", "in_usd":  3.00, "out_usd": 15.00},
    "anthropic:haiku-4.5":  {"unit": "per_mtok", "in_usd":  1.00, "out_usd":  5.00},

    # OpenAI — https://developers.openai.com/api/docs/pricing  (access 2026-04-21)
    "openai:gpt-5.4":       {"unit": "per_mtok", "in_usd":  2.50, "out_usd": 15.00},
    "openai:gpt-5.4-mini":  {"unit": "per_mtok", "in_usd":  0.75, "out_usd":  4.50},
    "openai:gpt-5.4-nano":  {"unit": "per_mtok", "in_usd":  0.20, "out_usd":  1.25},

    # Google — https://ai.google.dev/pricing  (access 2026-04-21)
    # gemini-2.5-pro tier shown is <=200k tokens; >200k = 2x input / 1.5x output.
    "google:gemini-2.5-pro":   {"unit": "per_mtok", "in_usd": 1.25, "out_usd": 10.00},
    "google:gemini-2.5-flash": {"unit": "per_mtok", "in_usd": 0.30, "out_usd":  2.50},
    # gemini_dive.py uses 'gemini:' prefix — alias for the same google: entries.
    "gemini:gemini-2.5-flash": {"unit": "per_mtok", "in_usd": 0.30, "out_usd":  2.50},
    "gemini:gemini-2.0-flash": {"unit": "per_mtok", "in_usd": 0.10, "out_usd":  0.40},
    "gemini:gemini-2.5-pro":   {"unit": "per_mtok", "in_usd": 1.25, "out_usd": 10.00},
    # Nano Banana — Gemini Image generation (per_request approximation; refine via metadata.image_count).
    "gemini:gemini-2.5-flash-image":         {"unit": "per_request", "usd": 0.039},
    "gemini:gemini-2.5-flash-image-preview": {"unit": "per_request", "usd": 0.039},
    "gemini:gemini-3.1-flash-image-preview": {"unit": "per_request", "usd": 0.045},
    "gemini:nano-banana-pro-preview":        {"unit": "per_request", "usd": 0.090},
    "gemini:gemini-3-pro-image-preview":     {"unit": "per_request", "usd": 0.120},

    # Free public APIs / scrape — no per-call cost; trace only.
    "reddit:json":   {"unit": "per_request", "usd": 0.000},
    "algolia:hn":    {"unit": "per_request", "usd": 0.000},
    "firebase:hn":   {"unit": "per_request", "usd": 0.000},
    "github:api":    {"unit": "per_request", "usd": 0.000},
    "nitter":        {"unit": "per_request", "usd": 0.000},

    # fal.ai — image upscale / face restore (per_request approximation, refine via fal pricing).
    "fal:clarity-upscaler": {"unit": "per_request", "usd": 0.020},
    "fal:gfpgan":           {"unit": "per_request", "usd": 0.005},
    "fal:codeformer":       {"unit": "per_request", "usd": 0.005},
    "fal:esrgan":           {"unit": "per_request", "usd": 0.003},
    "fal:aura-sr":          {"unit": "per_request", "usd": 0.005},
}


def _compute_cost(spec: dict, input_tokens: Optional[int], output_tokens: Optional[int]) -> float:
    """USD cost for one call given a COSTS entry. Raises on unknown unit / missing tokens."""
    unit = spec.get("unit")
    if unit == "per_request":
        return float(spec["usd"])
    if unit == "per_mtok":
        if input_tokens is None and output_tokens is None:
            raise ValueError(
                "[cost_log] per_mtok model requires input_tokens and/or "
                "output_tokens; got neither. Refusing to log cost=0 (DOCTRINE §2)."
            )
        in_tok = int(input_tokens or 0)
        out_tok = int(output_tokens or 0)
        cost = (in_tok / 1_000_000.0) * float(spec["in_usd"]) \
             + (out_tok / 1_000_000.0) * float(spec["out_usd"])
        return round(cost, 8)
    raise ValueError(f"[cost_log] unknown COSTS unit {unit!r}; fix the table.")


def log_call(
    tool: str,
    model: str,
    metadata: Optional[dict] = None,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
) -> Path:
    """Append a single JSON line to cost_log.jsonl. See module docstring for COSTS schema.

    Raises:
        RuntimeError: if log file's parent is not writable.
        TypeError: if metadata is not JSON-serializable.
        ValueError: per_mtok model called without token counts.
    """
    spec = COSTS.get(model)
    if spec is None:
        # Unknown model — do not silently default to 0. Surface it.
        sys.stderr.write(
            f"[cost_log] unknown model '{model}' — add to COSTS table in "
            f"{Path(__file__).name}; logging with cost_usd=null\n"
        )
        cost_usd = None
        unit = "unknown"
    else:
        cost_usd = _compute_cost(spec, input_tokens, output_tokens)
        unit = spec["unit"]

    entry = {
        "ts": time.time(),  # epoch seconds, float — cheap sort + range queries
        "ts_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "tool": tool,
        "model": model,
        "cost_usd": cost_usd,
        "unit": unit,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "metadata": metadata or {},
    }

    # Serialize first — catches TypeError before touching disk.
    line = json.dumps(entry, ensure_ascii=False) + "\n"

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(
            f"[cost_log] cannot create log directory {LOG_PATH.parent}: {e}"
        ) from e

    # Append mode. On POSIX this is atomic per-line if len(line) < PIPE_BUF
    # (4096 on Linux, 512 on macOS historically). Our lines are well under.
    # On Windows, append is serialized by the OS lock — concurrent writers are
    # also safe in practice for JSONL.
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        raise RuntimeError(
            f"[cost_log] write failed to {LOG_PATH}: {e}"
        ) from e

    return LOG_PATH


def total_cost_usd() -> float:
    """Quick aggregate for sanity checks. Skips entries with null cost."""
    if not LOG_PATH.exists():
        return 0.0
    total = 0.0
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                # A corrupt line is a real problem — surface it, don't absorb.
                raise RuntimeError(
                    f"[cost_log] corrupt JSONL line in {LOG_PATH}: {raw[:80]}"
                )
            c = entry.get("cost_usd")
            if isinstance(c, (int, float)):
                total += c
    return round(total, 6)


if __name__ == "__main__":
    # Manual smoke test: python tools/cost_log.py  (tests both schema paths)
    path = log_call(
        tool="smoke_test",
        model="browse:http",
        metadata={"note": "per_request path"},
    )
    print(f"per-request logged to: {path}")
    path = log_call(
        tool="smoke_test",
        model="anthropic:sonnet-4.6",
        input_tokens=10_000,
        output_tokens=2_000,
        metadata={"note": "per_mtok path"},
    )
    print(f"per-mtok logged to: {path}")
    print(f"running total: ${total_cost_usd():.6f}")

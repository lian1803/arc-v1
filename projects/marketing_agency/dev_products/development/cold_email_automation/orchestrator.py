"""
End-to-end orchestrator: 사람인 → 회사명 → 도메인 → 이메일 → Claude → Gmail SMTP → IMAP 분류.

§4 Delegate-by-Default: 각 단계 독립 실행.
§5 Real-Data: validator fence (score ≥ 75) 발송 전 강제.

CLI:
  python orchestrator.py collect --keyword "백엔드 개발자" --limit 30 --out leads.jsonl
  python orchestrator.py validate --leads leads.jsonl --out leads_verified.jsonl
  python orchestrator.py compose --leads leads_verified.jsonl --out drafts.jsonl
  python orchestrator.py send --drafts drafts.jsonl --max 30 --cadence
  python orchestrator.py route_replies

산업 무관: keyword 만 바꿔서 IT/마케팅/교육/의료/회계/제조 cover.
"""

import sys
import json
import argparse
from pathlib import Path

from collect_via_saramin import collect as collect_saramin
from composer import compose_email
from sender import send_with_log, RateLimiter, send_with_natural_cadence
from reply_router import route_replies as do_route_replies
from validate_lead import validate as validate_lead


def cmd_collect(args):
    out_path = Path(args.out)
    n_total = n_email = 0
    with open(out_path, "w", encoding="utf-8") as f:
        for lead in collect_saramin(args.keyword, args.limit, args.sleep):
            n_total += 1
            if lead.email:
                n_email += 1
            f.write(json.dumps({
                "company_name": lead.company_name,
                "csn": lead.csn,
                "homepage": lead.homepage,
                "email": lead.email,
                "email_confidence": lead.email_confidence,
                "source": lead.source,
                "fetched_at": lead.fetched_at,
            }, ensure_ascii=False) + "\n")
    pct = n_email * 100 // max(n_total, 1)
    print(f"collected {n_total} leads, {n_email} with email ({pct}%) → {out_path}")


def cmd_validate(args):
    """ Lead 4-check (홈피 alive / 회사명 매칭 / SMTP / WHOIS). score ≥ min-score 만 통과. """
    in_path = Path(args.leads)
    out_path = Path(args.out)
    n_total = n_pass = 0
    n_strong = n_medium = n_weak = 0

    with open(in_path, encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            lead = json.loads(line)
            n_total += 1
            result = validate_lead(lead)

            if result.overall_score >= 75:
                n_strong += 1
            elif result.overall_score >= 50:
                n_medium += 1
            else:
                n_weak += 1

            if result.overall_score >= args.min_score:
                n_pass += 1
                fout.write(json.dumps({
                    **lead,
                    "validation_score": result.overall_score,
                    "validation_notes": result.notes,
                }, ensure_ascii=False) + "\n")

    pct = n_pass * 100 // max(n_total, 1)
    print(
        f"validated {n_total}: STRONG {n_strong} / MEDIUM {n_medium} / WEAK {n_weak} | "
        f"pass (≥{args.min_score}): {n_pass} ({pct}%) → {out_path}"
    )


def cmd_compose(args):
    in_path, out_path = Path(args.leads), Path(args.out)
    n_total = n_ok = n_skip = 0

    with open(in_path, encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for line in fin:
            n_total += 1
            lead = json.loads(line)

            if not lead.get("email"):
                n_skip += 1
                continue

            try:
                draft = compose_email(
                    business_name=lead["company_name"],
                    industry=args.industry_hint or "사업자",
                    template=args.template,
                )
            except (ValueError, RuntimeError) as e:
                print(f"compose fail {lead['company_name']}: {e}", file=sys.stderr)
                n_skip += 1
                continue

            fout.write(json.dumps({
                "company_name": lead["company_name"],
                "to_email": lead["email"],
                "email_confidence": lead.get("email_confidence", 0),
                "validation_score": lead.get("validation_score", 0),
                "subject": draft.subject,
                "body": draft.body,
                "pain_estimate": draft.pain_estimate,
                "template": draft.template_used,
            }, ensure_ascii=False) + "\n")
            n_ok += 1

    print(f"composed {n_ok}/{n_total} drafts → {out_path} (skipped {n_skip})")


def cmd_send(args):
    in_path = Path(args.drafts)
    limiter = RateLimiter()
    initial_remaining = limiter.remaining()

    queued = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            if len(queued) >= args.max:
                break
            d = json.loads(line)
            # Optional fence: skip drafts with validation_score < min-score
            if d.get("validation_score", 100) < args.min_score:
                continue
            queued.append(d)

    if not queued:
        print(f"no drafts pass min_score {args.min_score}")
        return

    if args.cadence:
        sent = send_with_natural_cadence([
            {"to_email": d["to_email"], "subject": d["subject"], "body": d["body"],
             "business_name": d["company_name"]} for d in queued
        ])
        print(f"sent {len(sent)} emails (natural cadence)")
    else:
        n_sent = 0
        for d in queued:
            try:
                rec = send_with_log(d["to_email"], d["subject"], d["body"], d["company_name"])
                print(f"sent {d['to_email']} (remaining: {rec['remaining_today']})")
                n_sent += 1
            except RuntimeError as e:
                print(f"stop: {e}", file=sys.stderr)
                break
        print(f"sent {n_sent}/{initial_remaining} (cap)")


def cmd_route(args):
    n = do_route_replies()
    print(f"routed {n} replies")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect")
    c.add_argument("--keyword", required=True)
    c.add_argument("--limit", type=int, default=30)
    c.add_argument("--sleep", type=float, default=2.0)
    c.add_argument("--out", default="leads.jsonl")
    c.set_defaults(func=cmd_collect)

    c = sub.add_parser("validate", help="lead 4-check (§5 fence)")
    c.add_argument("--leads", required=True)
    c.add_argument("--out", default="leads_verified.jsonl")
    c.add_argument("--min-score", type=int, default=75, help="score ≥ N 통과 (75=STRONG)")
    c.set_defaults(func=cmd_validate)

    c = sub.add_parser("compose")
    c.add_argument("--leads", required=True)
    c.add_argument("--out", default="drafts.jsonl")
    c.add_argument("--template", default="short", choices=["short", "pain_first", "reference"])
    c.add_argument("--industry-hint", default=None)
    c.set_defaults(func=cmd_compose)

    c = sub.add_parser("send")
    c.add_argument("--drafts", required=True)
    c.add_argument("--max", type=int, default=30)
    c.add_argument("--cadence", action="store_true")
    c.add_argument("--min-score", type=int, default=0, help="validation_score < N skip (additional fence)")
    c.set_defaults(func=cmd_send)

    c = sub.add_parser("route_replies")
    c.set_defaults(func=cmd_route)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

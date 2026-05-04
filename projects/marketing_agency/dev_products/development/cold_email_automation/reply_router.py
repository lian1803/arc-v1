"""
답장 라우터 — IMAP 답장 fetch → Claude 분류 → 액션.

분류:
- interested: Slack 알림 + Lian 액션 대기
- question: Slack 알림
- not_interested: opt_out.txt 자동 추가
- spam: 무시 (silent)

§2 No-Silent-Fail: IMAP/Claude 에러 = raise.

환경변수: IMAP_SERVER / IMAP_USER / IMAP_PASS / ANTHROPIC_API_KEY / SLACK_WEBHOOK_URL (옵션)
모델: claude-haiku-4-5 (SPEC §6.1 Verification tier)
"""

import os
import json
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timezone
from pathlib import Path
import requests
from anthropic import Anthropic


REPLY_LOG = Path("cold_email_replies.jsonl")
OPT_OUT_PATH = Path("opt_out.txt")


CLASSIFY_PROMPT = """다음은 콜드 메일 답장입니다. 분류:

- interested: 미팅/통화 / 관심 / 견적 요청
- question: 구체 질문 (Pain / 가격 / 가능 여부)
- not_interested: 거절 / 관심 없음 / 이미 다른 곳
- spam: 자동 응답 / 광고 / out-of-office

JSON: {"category": "...", "summary": "한 줄 요약", "should_alert": true/false}
"""


def decode_email_header(value: str) -> str:
    parts = decode_header(value)
    out = []
    for p, c in parts:
        if isinstance(p, bytes):
            try:
                out.append(p.decode(c or "utf-8", errors="ignore"))
            except (LookupError, UnicodeDecodeError):
                out.append(p.decode("utf-8", errors="ignore"))
        else:
            out.append(p)
    return "".join(out)


class IMAPClient:
    def __init__(self):
        self.server = os.getenv("IMAP_SERVER")
        self.user = os.getenv("IMAP_USER")
        self.password = os.getenv("IMAP_PASS")
        if not all([self.server, self.user, self.password]):
            raise RuntimeError("IMAP_* 환경변수 미설정")

    def fetch_unread(self, mailbox: str = "INBOX", max_n: int = 100) -> list[dict]:
        m = imaplib.IMAP4_SSL(self.server)
        m.login(self.user, self.password)
        m.select(mailbox)

        _, data = m.search(None, "UNSEEN")
        ids = data[0].split()

        result = []
        for uid in ids[-max_n:]:
            _, msg_data = m.fetch(uid, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode("utf-8", errors="ignore")
                            break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="ignore")

            result.append({
                "uid": uid.decode() if isinstance(uid, bytes) else uid,
                "subject": decode_email_header(msg.get("Subject", "")),
                "from": decode_email_header(msg.get("From", "")),
                "body": body,
                "date": msg.get("Date", ""),
            })

        m.close()
        m.logout()
        return result


def classify(reply: dict) -> dict:
    client = Anthropic()
    user = (
        f"From: {reply['from']}\n"
        f"Subject: {reply['subject']}\n\n"
        f"{reply['body'][:2000]}"
    )

    msg = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=CLASSIFY_PROMPT,
        messages=[{"role": "user", "content": user}],
    )

    text = msg.content[0].text
    start = text.find("{")
    end = text.rfind("}")
    if start < 0:
        raise ValueError(f"no JSON: {text[:200]}")
    return json.loads(text[start:end + 1])


def slack_alert(reply: dict, category: str, summary: str) -> None:
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        return
    text = (
        f"*콜드메일 답장 ({category})*\n"
        f"From: {reply['from']}\n"
        f"Subject: {reply['subject']}\n"
        f"Summary: {summary}\n"
    )
    try:
        requests.post(webhook, json={"text": text}, timeout=10)
    except requests.RequestException as e:
        # Slack 알림 실패는 silent OK (메인 분류는 이미 log 됨)
        print(f"slack alert failed: {e}")


def add_to_opt_out(email_addr: str) -> None:
    addr = email_addr.strip()
    if not addr:
        return
    OPT_OUT_PATH.touch()
    existing = set()
    with open(OPT_OUT_PATH, encoding="utf-8") as f:
        existing = {l.strip().lower() for l in f}
    if addr.lower() not in existing:
        with open(OPT_OUT_PATH, "a", encoding="utf-8") as f:
            f.write(addr + "\n")


def route_replies() -> int:
    imap = IMAPClient()
    replies = imap.fetch_unread()
    n = 0
    for r in replies:
        try:
            cls = classify(r)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"classify fail uid={r['uid']}: {e}")
            continue

        cat = cls.get("category", "unknown")
        summary = cls.get("summary", "")

        rec = {
            "from": r["from"],
            "subject": r["subject"],
            "category": cat,
            "summary": summary,
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(REPLY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        if cat == "not_interested":
            add_to_opt_out(r["from"])
        elif cat in ("interested", "question"):
            slack_alert(r, cat, summary)
        # spam = silent skip
        n += 1
    return n


def main():
    n = route_replies()
    print(f"routed {n} replies")


if __name__ == "__main__":
    main()

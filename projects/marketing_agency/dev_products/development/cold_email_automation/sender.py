"""
콜드 메일 발송 — Gmail/네이버 SMTP (zero-signup, Lian 기존 계정).

§0 Money-First: 사업자 공개 이메일 only. 1일 30 cap = 형사 + 약관 risk 회피.
§2 No-Silent-Fail: SMTP / 한도 초과 = raise.

환경변수:
- SMTP_SERVER / SMTP_PORT / SMTP_USER / SMTP_PASS / SENDER_EMAIL
- OPT_OUT_REPLY_ADDRESS (수신거부 = 회신 = SMTP_USER 와 동일)

수신거부 = 회신 ("거부" 키워드) = reply_router.py 가 자동 opt-out 추가.
"""

import os
import json
import smtplib
import time
import random
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime, timezone
from pathlib import Path


DAILY_CAP = 30
LOG_PATH = Path("cold_email_log.jsonl")
OPT_OUT_PATH = Path("opt_out.txt")


class RateLimiter:
    def __init__(self, log_path: Path = LOG_PATH, cap: int = DAILY_CAP):
        self.log_path = log_path
        self.cap = cap

    def today_count(self) -> int:
        if not self.log_path.exists():
            return 0
        today = datetime.now(timezone.utc).date().isoformat()
        n = 0
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    if rec.get("date", "").startswith(today):
                        n += 1
                except json.JSONDecodeError:
                    continue
        return n

    def remaining(self) -> int:
        return max(0, self.cap - self.today_count())

    def check_or_raise(self) -> int:
        rem = self.remaining()
        if rem <= 0:
            raise RuntimeError(
                f"daily cap {self.cap} hit. §0 형사 risk + Gmail 약관 보호."
            )
        return rem


def is_opted_out(email: str) -> bool:
    if not OPT_OUT_PATH.exists():
        return False
    with open(OPT_OUT_PATH, encoding="utf-8") as f:
        return email.strip().lower() in {l.strip().lower() for l in f}


class SMTPSender:
    """ Gmail / 네이버 SMTP (Lian 기존 계정 + App Password). """

    def __init__(self):
        self.server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASS")
        self.sender_email = os.getenv("SENDER_EMAIL", self.user)

        if not all([self.user, self.password]):
            raise RuntimeError(
                "SMTP_USER / SMTP_PASS 미설정. setup_guide.md §1 (Gmail App Password)."
            )

        self.opt_out_reply = os.getenv("OPT_OUT_REPLY_ADDRESS", self.sender_email)

    def send(self, to_email: str, subject: str, body: str, business_name: str = "") -> dict:
        # 한국 정통법 footer (회신=거부 패턴, 가입 0 가능)
        full_body = (
            f"{body}\n\n"
            f"---\n"
            f"본 메일은 사업자 공개 이메일 ({to_email}) 로 발송되었습니다.\n"
            f"수신을 원치 않으시면 본 메일에 \"거부\" 라고 회신해 주세요.\n"
            f"({self.opt_out_reply} 로 자동 opt-out 처리됩니다.)\n"
        )

        msg = MIMEText(full_body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = formataddr(("", self.sender_email))
        msg["To"] = to_email

        with smtplib.SMTP(self.server, self.port, timeout=30) as s:
            s.ehlo()
            s.starttls()
            s.login(self.user, self.password)
            s.sendmail(self.sender_email, [to_email], msg.as_string())

        return {
            "to": to_email,
            "business_name": business_name,
            "subject": subject,
            "sender": self.sender_email,
            "date": datetime.now(timezone.utc).isoformat(),
        }


def send_with_log(to_email: str, subject: str, body: str, business_name: str = "") -> dict:
    if is_opted_out(to_email):
        raise RuntimeError(f"opted out: {to_email}")

    limiter = RateLimiter()
    remaining = limiter.check_or_raise()

    sender = SMTPSender()
    record = sender.send(to_email, subject, body, business_name)

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    record["remaining_today"] = remaining - 1

    # 자연 cadence — Gmail 자동발송 패턴 회피 (60-180초 랜덤)
    delay = random.randint(60, 180)
    record["next_send_after_seconds"] = delay
    return record


def send_with_natural_cadence(records: list[dict]) -> list[dict]:
    """ 여러 메일 발송 시 60-180초 랜덤 sleep 자연 cadence. """
    sent = []
    for i, rec in enumerate(records):
        if i > 0:
            time.sleep(random.randint(60, 180))
        result = send_with_log(
            rec["to_email"], rec["subject"], rec["body"], rec.get("business_name", ""),
        )
        sent.append(result)
    return sent


def main():
    """CLI: python sender.py to@example.com "Subject" "Body" [business_name]"""
    import sys

    if len(sys.argv) < 4:
        print("usage: python sender.py <to_email> <subject> <body> [business_name]")
        sys.exit(1)

    to = sys.argv[1]
    subject = sys.argv[2]
    body = sys.argv[3]
    name = sys.argv[4] if len(sys.argv) > 4 else ""

    rec = send_with_log(to, subject, body, name)
    print(json.dumps(rec, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

"""
위시켓/크몽 입찰 초안 -> 이메일 알림
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

GMAIL_ADDRESS = os.environ.get("SMTP_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("SMTP_PASS", "")
LIAN_EMAIL = os.environ.get("LIAN_NOTIFY_EMAIL", GMAIL_ADDRESS)


def format_body(listings_with_bids: list[dict]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    platforms = list({item.get("platform", "?") for item in listings_with_bids})
    lines = [
        f"[자동입찰] {'+'.join(platforms)} 새 의뢰 {len(listings_with_bids)}건 ({now})",
        "=" * 60,
        "",
        "각 입찰글을 복사해 해당 플랫폼 입찰하기에 붙여넣기 하세요.",
        "",
    ]

    for i, item in enumerate(listings_with_bids, 1):
        platform = item.get("platform", "?")
        lines += [
            f"━━━ {i}. [{platform}] {item['title']}",
            f"예산: {item.get('budget_text', '')} | 기간: {item.get('duration', '')}",
            f"링크: {item['url']}",
            "",
            "[ 입찰글 초안 - 복사 후 붙여넣기 ]",
            "-" * 40,
            item["bid_text"],
            "-" * 40,
            "",
        ]

    lines.append("ARC dev_products 자동 생성")
    return "\n".join(lines)


def send_notification(listings_with_bids: list[dict]) -> bool:
    if not listings_with_bids:
        print("발송할 의뢰글 없음.")
        return True

    body = format_body(listings_with_bids)

    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        import sys
        print("[NOTICE] SMTP 미설정. 콘솔 출력:")
        out = sys.stdout.buffer if hasattr(sys.stdout, "buffer") else None
        if out:
            out.write(body.encode("utf-8", errors="replace") + b"\n")
        else:
            print(body.encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
        return True

    platforms = list({item.get("platform", "?") for item in listings_with_bids})
    subject = f"[자동입찰] {'+'.join(platforms)} {len(listings_with_bids)}건 초안 준비"

    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = LIAN_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            smtp.sendmail(GMAIL_ADDRESS, LIAN_EMAIL, msg.as_string())
        print(f"발송 완료 -> {LIAN_EMAIL} ({len(listings_with_bids)}건)")
        return True
    except Exception as e:
        print(f"[ERROR] 발송 실패: {e}")
        return False


if __name__ == "__main__":
    test_items = [{
        "title": "쇼핑몰 자동화",
        "category": "자동화",
        "budget_text": "100-150만",
        "platform": "위시켓",
        "url": "https://www.wishket.com/project/test/",
        "bid_text": "자동화 가능합니다. 7일 납기, 120만원.",
    }]
    send_notification(test_items)

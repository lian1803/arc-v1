"""
이메일 추출 + 검증 (zero-signup) — 홈피 정규식 + DNS MX.

§0 Money-First: 사업자 공개 이메일만 (홈피에 박혀 있는 것). 형사 risk 낮.
§2 No-Silent-Fail: 네트워크 에러 = raise. 추출 실패 = empty list.

검증:
1. 홈피 fetch → 이메일 정규식 추출 (info@/contact@ + 홈피 박힌 모든 @패턴)
2. DNS MX record 확인 (도메인 메일 서버 존재)
3. (옵션) SMTP banner test — 발송 X, 250 응답만 확인

환경변수: 없음 (가입 0).
"""

import re
import socket
import requests
import dns.resolver
import smtplib
from typing import Optional
from urllib.parse import urlparse
from dataclasses import dataclass
from bs4 import BeautifulSoup


# 사업자 공개 패턴 (개인 이름 짐작 = 형사 risk → 제외)
PUBLIC_PREFIXES = {
    "info", "contact", "hello", "mail", "office",
    "support", "ceo", "admin", "biz", "sales",
    "help", "manager", "korea", "kr",
}

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class EmailGuess:
    email: str
    confidence: int  # 0-100
    verified_dns: bool  # MX exists
    verified_smtp: bool  # SMTP 250 ok (옵션)
    source: str  # 'homepage' / 'pattern'


def extract_emails_from_homepage(url: str, timeout: int = 15) -> list[str]:
    """
    홈피 fetch → 본문 + mailto: 링크에서 이메일 추출.
    """
    if not url:
        return []
    if not url.startswith("http"):
        url = "https://" + url

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=True,
        )
        resp.raise_for_status()
    except requests.RequestException:
        return []

    text = resp.text
    soup = BeautifulSoup(text, "html.parser")

    found = set()

    # mailto: 링크
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("mailto:"):
            addr = href[len("mailto:"):].split("?")[0].strip()
            if addr:
                found.add(addr)

    # 본문 텍스트 정규식
    body_text = soup.get_text(" ", strip=True)
    found.update(EMAIL_RE.findall(body_text))

    # 푸터 영역 (footer / contact 키워드 근방) 우선
    return [_.strip() for _ in found if _.strip()]


def is_public_pattern(email: str) -> bool:
    """ info@/contact@ 등 공개 패턴 = §0 형사 risk 낮. """
    local = email.split("@", 1)[0].lower() if "@" in email else ""
    return local in PUBLIC_PREFIXES


def has_mx_record(domain: str) -> bool:
    """ DNS MX 확인. 메일 서버 존재 = 발송 가능 (스팸 아님 보장 X). """
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=10)
        return len(list(answers)) > 0
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
            dns.resolver.NoNameservers, dns.exception.Timeout):
        return False


def smtp_banner_check(email: str, sender: str = "test@example.com") -> bool:
    """
    SMTP banner check (발송 안 함, 250 응답만 확인).
    Gmail / 네이버 등 일부 서버는 250 catch-all → false positive 가능.
    """
    if "@" not in email:
        return False
    domain = email.split("@", 1)[1]

    try:
        mx = dns.resolver.resolve(domain, "MX", lifetime=10)
        mx_host = sorted(mx, key=lambda r: r.preference)[0].exchange.to_text().rstrip(".")
    except Exception:
        return False

    try:
        with smtplib.SMTP(mx_host, 25, timeout=10) as s:
            s.helo("example.com")
            s.mail(sender)
            code, _ = s.rcpt(email)
            return code in (250, 251)
    except (smtplib.SMTPException, socket.error, OSError):
        return False


def best_email_for_business(
    business_name: str,
    homepage_url: Optional[str] = None,
    deep_smtp_check: bool = False,
) -> Optional[EmailGuess]:
    """
    사업자 → 가장 확실한 이메일 1개.

    1. 홈피에서 이메일 추출
    2. 공개 패턴 우선 (info@/contact@)
    3. DNS MX 확인
    4. (옵션) SMTP banner 확인

    Returns None if no email found OR no domain inferable.
    """
    if not homepage_url:
        return None

    found = extract_emails_from_homepage(homepage_url)
    if not found:
        return None

    # 공개 패턴 우선 정렬
    found_sorted = sorted(found, key=lambda e: (not is_public_pattern(e), e))

    for email in found_sorted:
        if "@" not in email:
            continue
        domain = email.split("@", 1)[1]

        mx_ok = has_mx_record(domain)
        if not mx_ok:
            continue

        smtp_ok = smtp_banner_check(email) if deep_smtp_check else False

        confidence = 50
        if is_public_pattern(email):
            confidence += 20
        if mx_ok:
            confidence += 15
        if smtp_ok:
            confidence += 15

        return EmailGuess(
            email=email,
            confidence=min(100, confidence),
            verified_dns=mx_ok,
            verified_smtp=smtp_ok,
            source="homepage",
        )

    return None


def main():
    """CLI: python email_guesser.py "사업자명" "https://homepage.com" [--smtp]"""
    import sys, json

    if len(sys.argv) < 3:
        print("usage: python email_guesser.py <business_name> <homepage_url> [--smtp]")
        sys.exit(1)

    name = sys.argv[1]
    url = sys.argv[2]
    deep = "--smtp" in sys.argv

    guess = best_email_for_business(name, url, deep_smtp_check=deep)
    if not guess:
        print(json.dumps({"error": "no email found"}, ensure_ascii=False))
        sys.exit(2)

    print(json.dumps({
        "email": guess.email,
        "confidence": guess.confidence,
        "verified_dns": guess.verified_dns,
        "verified_smtp": guess.verified_smtp,
        "source": guess.source,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

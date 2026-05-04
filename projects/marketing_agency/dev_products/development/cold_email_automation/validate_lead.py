"""
Lead 검증기 — 발송 전 4 check (§5 Real-Data-Only enforcement).

§5 Real-Data: 회사명/도메인/이메일 verified or 라벨.
§2 No-Silent-Fail: 검증 실패 = explicit fail score, raise 안 함 (집계 위해).

4 check:
1. 회사명 ↔ 홈페이지 본문 매칭
2. 이메일 SMTP deliverability (banner 250)
3. 도메인 WHOIS 등록자 ↔ 회사명 매칭 (.co.kr KISA)
4. Homepage 200 응답 + 한국어 텍스트

CLI: python validate_lead.py leads.jsonl > validation.jsonl
"""

import re
import sys
import json
import socket
import smtplib
import subprocess
import requests
import dns.resolver
from dataclasses import dataclass, asdict
from pathlib import Path


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
    "Accept": "text/html,*/*;q=0.8",
}


@dataclass
class ValidationResult:
    company_name: str
    domain: str
    email: str
    homepage_alive: bool = False
    name_in_homepage: bool = False
    email_deliverable: bool = False
    whois_match: bool = False
    overall_score: int = 0  # 0-100
    notes: list[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


def normalize_company_name(name: str) -> list[str]:
    """ 회사명 → 검증용 키워드 list. (주)X → X 제거 + 영문/한글 조각. """
    name = re.sub(r"\(주\)|주식회사|㈜|Co\.|Ltd\.?", "", name).strip()
    name = name.replace("(", " ").replace(")", " ")
    parts = [p for p in re.split(r"\s+", name) if len(p) >= 2]
    return parts


def check_homepage_alive(domain: str) -> tuple[bool, str]:
    """ 홈피 200 + 한국어 본문 OR 영문이라도 200 = alive. """
    for proto in ("https://", "http://"):
        url = f"{proto}{domain}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        except requests.RequestException as e:
            continue
        if r.status_code == 200 and len(r.text) > 500:
            return True, r.text
    return False, ""


def check_name_in_homepage(name_keywords: list[str], html: str) -> bool:
    """ 회사명 키워드 중 1개라도 homepage 본문에 박혀 있나 """
    if not html:
        return False
    text_lower = html.lower()
    for kw in name_keywords:
        if kw.lower() in text_lower:
            return True
    return False


def check_email_deliverable(email: str) -> tuple[bool, str]:
    """
    SMTP banner check — 발송 X, 250 응답만.
    Catch-all 도메인 (Gmail 등) 은 false positive 가능.
    """
    if "@" not in email:
        return False, "invalid email format"

    domain = email.split("@", 1)[1]

    try:
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=10)
        mx_host = sorted(mx_records, key=lambda r: r.preference)[0].exchange.to_text().rstrip(".")
    except Exception as e:
        return False, f"no MX: {type(e).__name__}"

    try:
        with smtplib.SMTP(mx_host, 25, timeout=15) as s:
            s.helo("validator.local")
            s.mail("validator@example.com")
            code, _ = s.rcpt(email)
            return (code in (250, 251)), f"SMTP {code}"
    except (smtplib.SMTPException, socket.error, OSError) as e:
        return False, f"SMTP err: {type(e).__name__}"


def check_whois(domain: str) -> tuple[bool, str]:
    """
    .co.kr / .kr WHOIS 조회 — 등록자 (사업자명) 추출.
    Windows whois 명령 없을 수도 있어 socket fallback.
    """
    try:
        # Korea KISA WHOIS server: whois.kr (port 43)
        whois_server = "whois.kr" if domain.endswith((".kr", ".co.kr")) else "whois.iana.org"
        with socket.create_connection((whois_server, 43), timeout=10) as s:
            s.sendall((domain + "\r\n").encode("utf-8"))
            response = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
        text = response.decode("utf-8", errors="ignore")
        return True, text
    except (socket.error, OSError) as e:
        return False, f"WHOIS err: {type(e).__name__}"


def check_whois_match(name_keywords: list[str], whois_text: str) -> bool:
    """ WHOIS 응답에 회사명 키워드 박혀 있나 """
    if not whois_text:
        return False
    text_lower = whois_text.lower()
    for kw in name_keywords:
        if kw.lower() in text_lower:
            return True
    return False


def validate(lead: dict) -> ValidationResult:
    name = lead.get("company_name") or lead.get("business_name") or ""
    domain = lead.get("homepage", "") or ""
    email = lead.get("email") or ""

    # Strip URL parts
    if domain.startswith("http"):
        domain = re.sub(r"https?://(?:www\.)?", "", domain).split("/")[0]
    elif domain.startswith("www."):
        domain = domain[4:]

    result = ValidationResult(company_name=name, domain=domain, email=email)
    keywords = normalize_company_name(name)

    if not domain:
        result.notes.append("no domain")
        return result

    alive, html = check_homepage_alive(domain)
    result.homepage_alive = alive
    if not alive:
        result.notes.append("homepage dead/blocked")

    if alive:
        result.name_in_homepage = check_name_in_homepage(keywords, html)
        if not result.name_in_homepage:
            result.notes.append(f"name '{name}' NOT in homepage body")

    if email:
        deliverable, smtp_note = check_email_deliverable(email)
        result.email_deliverable = deliverable
        result.notes.append(f"email: {smtp_note}")

    whois_ok, whois_text = check_whois(domain)
    if whois_ok:
        result.whois_match = check_whois_match(keywords, whois_text)
        if not result.whois_match:
            result.notes.append("WHOIS owner ≠ company name")

    # Score 0-100
    score = 0
    if result.homepage_alive: score += 25
    if result.name_in_homepage: score += 30
    if result.email_deliverable: score += 25
    if result.whois_match: score += 20
    result.overall_score = score

    return result


def main():
    if len(sys.argv) < 2:
        print("usage: python validate_lead.py <leads.jsonl> [--verbose]")
        sys.exit(1)

    in_path = Path(sys.argv[1])
    verbose = "--verbose" in sys.argv

    n_total = 0
    n_strong = 0  # ≥75
    n_medium = 0  # 50-74
    n_weak = 0    # <50

    with open(in_path, encoding="utf-8") as f:
        for line in f:
            lead = json.loads(line)
            n_total += 1
            result = validate(lead)

            if result.overall_score >= 75:
                n_strong += 1
                tier = "STRONG"
            elif result.overall_score >= 50:
                n_medium += 1
                tier = "MEDIUM"
            else:
                n_weak += 1
                tier = "WEAK"

            print(json.dumps({
                **asdict(result),
                "tier": tier,
            }, ensure_ascii=False))

            if verbose:
                marks = (
                    f"alive={'Y' if result.homepage_alive else 'N'} "
                    f"name={'Y' if result.name_in_homepage else 'N'} "
                    f"smtp={'Y' if result.email_deliverable else 'N'} "
                    f"whois={'Y' if result.whois_match else 'N'}"
                )
                print(
                    f"  {tier:6} {result.overall_score:3}/100 | "
                    f"{result.company_name[:25]:25} | {marks} | "
                    f"{', '.join(result.notes[:2])}",
                    file=sys.stderr,
                )

    print(
        f"\n# TOTAL {n_total}: STRONG {n_strong} / MEDIUM {n_medium} / WEAK {n_weak}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()

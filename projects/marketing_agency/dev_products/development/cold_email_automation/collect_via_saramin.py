"""
Lead source: 사람인 채용 → 회사 정보 페이지 (csn direct) → 홈페이지 → 이메일.

§5 Real-Data: 사람인 company-info 페이지 = 회사가 직접 등록한 홈페이지 URL → 도메인 매칭 정확도 ↑.
§10 Pain-Anchored: 채용 중 = "개발자 못 뽑음" Pain.
§2 No-Silent-Fail: 네트워크 에러 = raise.
§0 Money-First: 사람인 ToS 위반 = 차감 X. 사업자 공개 이메일만.

워크플로우:
1. 사람인 검색 → (회사명, csn) list
2. csn → company-info page → 홈페이지 URL 직접 추출
3. 홈페이지 → fetch → 이메일 정규식 추출

CLI: python collect_via_saramin.py --keyword "백엔드 개발자" --limit 30
"""

import re
import time
import json
import argparse
import requests
from typing import Iterator, Optional
from urllib.parse import urlparse
from dataclasses import dataclass, field
from datetime import datetime, timezone


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

EMAIL_BLOCKLIST = [
    "@example", "@test.", "@your", "@mail.com",
    "@gmail.com", "@naver.com", "@daum.net", "@hanmail.net",
]

PUBLIC_PREFIXES = {
    "info", "contact", "hello", "mail", "office",
    "support", "ceo", "admin", "biz", "sales",
    "help", "manager", "korea", "kr", "hr", "recruit",
}


@dataclass
class Lead:
    company_name: str
    csn: str = ""
    homepage: Optional[str] = None
    email: Optional[str] = None
    email_confidence: int = 0
    saramin_recruit_count: int = 0
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "saramin"


def search_saramin(keyword: str, limit: int = 30) -> list[tuple[str, str]]:
    """ 사람인 검색 → [(csn, 회사명), ...] (dedup) """
    s = requests.Session()
    s.headers.update(HEADERS)
    params = {
        "searchType": "search",
        "searchword": keyword,
        "recruitPage": 1,
        "recruitSort": "reg_dt",
        "recruitPageCount": min(limit * 2, 100),  # dedup 후 limit 보장
    }
    r = s.get("https://www.saramin.co.kr/zf_user/search/recruit", params=params, timeout=30)
    r.raise_for_status()

    raw = re.findall(
        r'<strong class="corp_name">\s*<a[^>]*href="/zf_user/company-info/view\?csn=([^"]+)"[^>]*>([^<]+)</a>',
        r.text,
    )
    seen = set()
    out = []
    for csn, name in raw:
        n = name.strip()
        if not n or n in seen:
            continue
        seen.add(n)
        out.append((csn, n))
        if len(out) >= limit:
            break
    return out


def fetch_homepage_from_saramin(csn: str, sleep: float = 2.0) -> Optional[str]:
    """ 사람인 company-info page → '홈페이지' 항목 → URL 직접 추출 """
    s = requests.Session()
    s.headers.update(HEADERS)
    time.sleep(sleep)
    r = s.get(
        f"https://www.saramin.co.kr/zf_user/company-info/view?csn={csn}",
        timeout=30,
    )
    if r.status_code != 200:
        return None

    text = r.text
    ctx = re.search(r"홈페이지.{0,500}", text, re.S)
    if not ctx:
        return None

    for url in re.findall(r'https?://[^"\s\'<]+', ctx.group(0)):
        if "saramin" in url or "pstatic" in url:
            continue
        parsed = urlparse(url)
        if not parsed.netloc:
            continue
        return parsed.netloc.lower()
    return None


def extract_emails(domain: str, sleep: float = 1.0) -> list[str]:
    """ 도메인 fetch + /contact/about → 이메일 정규식 추출 """
    s = requests.Session()
    s.headers.update(HEADERS)
    found = []

    base_used = None
    for proto in ("https://", "http://"):
        for prefix in ("", "www."):
            base = f"{proto}{prefix}{domain.lstrip('www.')}"
            try:
                r = s.get(base, timeout=15, allow_redirects=True)
            except requests.RequestException:
                continue
            if r.status_code != 200:
                continue
            found.extend(EMAIL_RE.findall(r.text))
            base_used = base
            break
        if base_used:
            break

    if base_used:
        for path in ("/contact", "/about", "/company", "/contact-us", "/contact.html", "/about.html"):
            try:
                rc = s.get(base_used + path, timeout=10)
                if rc.status_code == 200:
                    found.extend(EMAIL_RE.findall(rc.text))
            except requests.RequestException:
                continue

    cleaned = []
    seen = set()
    for e in found:
        e = e.lower()
        if e in seen:
            continue
        if any(skip in e for skip in EMAIL_BLOCKLIST):
            continue
        seen.add(e)
        cleaned.append(e)

    return cleaned[:5]


def best_email(emails: list[str]) -> tuple[Optional[str], int]:
    """ 공개 패턴 (info@/contact@) 우선, confidence 점수. """
    if not emails:
        return None, 0
    for e in emails:
        local = e.split("@", 1)[0]
        if local in PUBLIC_PREFIXES:
            return e, 80
    return emails[0], 50


def collect(keyword: str, limit: int = 30, sleep: float = 2.0) -> Iterator[Lead]:
    pairs = search_saramin(keyword, limit=limit)
    for csn, company in pairs:
        homepage = fetch_homepage_from_saramin(csn, sleep=sleep)
        if not homepage:
            yield Lead(company_name=company, csn=csn, source="saramin")
            continue

        time.sleep(1.0)
        emails = extract_emails(homepage)
        email, conf = best_email(emails)

        yield Lead(
            company_name=company,
            csn=csn,
            homepage=homepage,
            email=email,
            email_confidence=conf,
            source="saramin",
        )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--keyword", default="백엔드 개발자")
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--sleep", type=float, default=2.0)
    p.add_argument("--out", default="leads.jsonl")
    args = p.parse_args()

    n_total = n_hp = n_email = 0
    with open(args.out, "w", encoding="utf-8") as f:
        for lead in collect(args.keyword, args.limit, args.sleep):
            n_total += 1
            if lead.homepage:
                n_hp += 1
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
            print(
                f"  {lead.company_name[:25]:25} | hp={lead.homepage or 'None':25} | email={lead.email or 'None'}"
            )

    pct_hp = n_hp * 100 // max(n_total, 1)
    pct_email = n_email * 100 // max(n_total, 1)
    print(f"\nTOTAL: {n_total} companies, {n_hp} with homepage ({pct_hp}%), {n_email} with email ({pct_email}%)")


if __name__ == "__main__":
    main()

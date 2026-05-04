#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIANCP 에이전시 경량 CRM 시스템"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Windows 인코딩 설정
if sys.stdout.encoding is None:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

CRM_PATH = Path(__file__).parent.parent / "data" / "crm.json"

PACKAGE_PRICES = {
    "Growth Starter": 700000,
    "Growth Plus": 3300000,
    "Full Stack": 8000000,
}

LEAD_STATUSES = [
    "리드발굴",
    "진단완료_미계약",
    "제안완료",
    "협상중",
    "계약완료",
    "드롭"
]

CLIENT_STATUSES = [
    "운영중",
    "일시정지",
    "해지",
    "갱신협상중"
]


def load() -> dict:
    """CRM 데이터 로드. 파일 없으면 초기 구조 생성."""
    if not CRM_PATH.exists():
        return {"clients": [], "leads": []}

    try:
        with open(CRM_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"clients": [], "leads": []}


def save(data: dict):
    """CRM 데이터 저장."""
    CRM_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CRM_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _next_lead_id(data: dict) -> str:
    """다음 리드 ID 생성."""
    if not data["leads"]:
        return "l001"
    max_num = max(int(lead["id"][1:]) for lead in data["leads"])
    return f"l{max_num + 1:03d}"


def _next_client_id(data: dict) -> str:
    """다음 클라이언트 ID 생성."""
    if not data["clients"]:
        return "c001"
    max_num = max(int(client["id"][1:]) for client in data["clients"])
    return f"c{max_num + 1:03d}"


def add_lead(brand_name: str, score: int, grade: str, recommended_package: str,
             smartstore_url: str = "", insta_handle: str = "", notes: str = "") -> str:
    """진단 완료 후 리드 등록. 자동 ID 생성. lead_id 반환."""
    data = load()

    lead_id = _next_lead_id(data)
    today = datetime.now().strftime("%Y-%m-%d")

    new_lead = {
        "id": lead_id,
        "brand_name": brand_name,
        "diagnosis_score": score,
        "grade": grade,
        "recommended_package": recommended_package,
        "status": "진단완료_미계약",
        "contacted_at": today,
        "follow_up_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "notes": notes,
        "smartstore_url": smartstore_url,
        "insta_handle": insta_handle
    }

    data["leads"].append(new_lead)
    save(data)

    return lead_id


def convert_to_client(lead_id: str, package: str, monthly_fee: int,
                       contact: str = "", email: str = "", ad_budget: int = 0,
                       vendor: str = "", salesperson: str = "리안") -> str:
    """리드를 계약 클라이언트로 전환. client_id 반환."""
    data = load()

    # 리드 찾기
    lead = None
    lead_idx = None
    for idx, l in enumerate(data["leads"]):
        if l["id"] == lead_id:
            lead = l
            lead_idx = idx
            break

    if not lead:
        raise ValueError(f"리드 {lead_id} 없음")

    client_id = _next_client_id(data)
    today = datetime.now().strftime("%Y-%m-%d")
    next_review = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")

    new_client = {
        "id": client_id,
        "brand_name": lead["brand_name"],
        "contact": contact,
        "email": email,
        "package": package,
        "monthly_fee": monthly_fee,
        "ad_budget": ad_budget,
        "start_date": today,
        "status": "운영중",
        "salesperson": salesperson,
        "vendor": vendor,
        "diagnosis_score": lead["diagnosis_score"],
        "next_review": next_review,
        "lead_id": lead_id
    }

    data["clients"].append(new_client)

    # 리드 상태 업데이트
    data["leads"][lead_idx]["status"] = "계약완료"

    save(data)

    return client_id


def update_lead_status(lead_id: str, new_status: str, follow_up_date: str = "", notes: str = ""):
    """리드 상태 업데이트."""
    if new_status not in LEAD_STATUSES:
        raise ValueError(f"유효하지 않은 상태: {new_status}")

    data = load()

    for lead in data["leads"]:
        if lead["id"] == lead_id:
            lead["status"] = new_status
            if follow_up_date:
                lead["follow_up_date"] = follow_up_date
            if notes:
                lead["notes"] = notes
            save(data)
            return

    raise ValueError(f"리드 {lead_id} 없음")


def get_follow_ups_today() -> list:
    """오늘 팔로업 해야 할 리드 목록. 날짜 기준 필터링."""
    data = load()
    today = datetime.now().strftime("%Y-%m-%d")

    return [
        lead for lead in data["leads"]
        if lead["follow_up_date"] == today and lead["status"] != "드롭"
    ]


def get_follow_ups_this_week() -> list:
    """이번 주 팔로업 리드 목록."""
    data = load()
    today = datetime.now()
    week_start = today
    week_end = today + timedelta(days=6)

    results = []
    for lead in data["leads"]:
        try:
            fup_date = datetime.strptime(lead["follow_up_date"], "%Y-%m-%d")
            if week_start <= fup_date <= week_end and lead["status"] != "드롭":
                results.append(lead)
        except ValueError:
            continue

    return sorted(results, key=lambda x: x["follow_up_date"])


def get_renewal_alerts() -> list:
    """계약 갱신 14일 이내인 클라이언트 목록 (next_review 기준)."""
    data = load()
    today = datetime.now()
    alert_date = today + timedelta(days=14)

    results = []
    for client in data["clients"]:
        if client["status"] == "운영중":
            try:
                review_date = datetime.strptime(client["next_review"], "%Y-%m-%d")
                if today <= review_date <= alert_date:
                    results.append(client)
            except ValueError:
                continue

    return sorted(results, key=lambda x: x["next_review"])


def get_active_clients() -> list:
    """현재 운영중인 클라이언트 목록."""
    data = load()
    return [client for client in data["clients"] if client["status"] == "운영중"]


def get_pipeline_summary() -> dict:
    """전체 파이프라인 현황."""
    data = load()

    # 상태별 리드 카운트
    by_status = {}
    for status in LEAD_STATUSES:
        count = len([l for l in data["leads"] if l["status"] == status])
        by_status[status] = count

    # 운영중 클라이언트 월 매출
    active_clients = get_active_clients()
    monthly_revenue = sum(client["monthly_fee"] for client in active_clients)

    # 협상중 리드의 예상 매출
    negotiation_leads = [l for l in data["leads"] if l["status"] == "협상중"]
    pipeline_value = sum(
        PACKAGE_PRICES.get(l["recommended_package"], 0)
        for l in negotiation_leads
    )

    return {
        "total_leads": len(data["leads"]),
        "by_status": by_status,
        "active_clients": len(active_clients),
        "monthly_revenue": monthly_revenue,
        "pipeline_value": pipeline_value
    }


def _format_currency(value: int) -> str:
    """숫자를 한국 통화 형식으로 표시."""
    if value >= 10000000:
        return f"{value // 1000000:.1f}백만원"
    elif value >= 1000000:
        return f"{value // 1000000:.1f}백만원"
    elif value >= 10000:
        return f"{value // 10000:.0f}만원"
    else:
        return f"{value:,}원"


def _days_until(target_date_str: str) -> int:
    """특정 날짜까지 며칠 남았는지 계산."""
    try:
        target = datetime.strptime(target_date_str, "%Y-%m-%d")
        today = datetime.now()
        delta = (target - today).days
        return delta
    except ValueError:
        return 0


def print_dashboard():
    """터미널 대시보드 출력."""
    today_str = datetime.now().strftime("%Y-%m-%d")

    print("\n" + "=" * 40)
    print("  LIANCP 에이전시 CRM 대시보드")
    print(f"  {today_str}")
    print("=" * 40 + "\n")

    # 오늘 팔로업
    today_followups = get_follow_ups_today()
    print(f"[오늘 팔로업] ({len(today_followups)}건)")
    if today_followups:
        for lead in today_followups:
            print(f"  - {lead['brand_name']} | {lead['status']} ({lead['recommended_package']} 추천)")
    else:
        print("  없음")

    print()

    # 운영중 클라이언트
    active = get_active_clients()
    summary = get_pipeline_summary()
    monthly_revenue = summary["monthly_revenue"]

    print(f"[운영중 클라이언트] ({len(active)}개)")
    print(f"  월 매출: {_format_currency(monthly_revenue)}")
    if active:
        for client in active[:5]:  # 최대 5개만 표시
            days_left = _days_until(client["next_review"])
            print(f"  - {client['brand_name']} | {client['package']} ({_format_currency(client['monthly_fee'])})")
        if len(active) > 5:
            print(f"  ... 외 {len(active) - 5}개")

    print()

    # 파이프라인
    print("[파이프라인]")
    by_status = summary["by_status"]
    total = summary["total_leads"]
    negotiation_count = by_status.get("협상중", 0)
    pipeline_value = summary["pipeline_value"]

    print(f"  총 리드: {total}개")
    if negotiation_count > 0:
        print(f"  협상중: {negotiation_count}개 (예상 파이프라인: {_format_currency(pipeline_value)})")

    print()

    # 갱신 알림
    renewals = get_renewal_alerts()
    print(f"[갱신 알림] ({len(renewals)}건)")
    if renewals:
        for client in renewals:
            days_left = _days_until(client["next_review"])
            print(f"  - {client['brand_name']} | {client['next_review']} 갱신 (D-{days_left})")
    else:
        print("  없음")

    print("\n" + "=" * 40 + "\n")


def print_leads(status_filter: Optional[str] = None):
    """리드 목록 출력."""
    data = load()
    leads = data["leads"]

    if status_filter:
        leads = [l for l in leads if l["status"] == status_filter]

    if not leads:
        print("리드가 없습니다.")
        return

    print(f"\n총 {len(leads)}개의 리드\n")
    print(f"{'ID':<6} {'브랜드':<20} {'점수':<6} {'등급':<4} {'상태':<15} {'팔로업':<12}")
    print("-" * 75)

    for lead in leads:
        brand_name = lead['brand_name'][:20]
        status = lead['status'][:15]
        print(f"{lead['id']:<6} {brand_name:<20} {lead['diagnosis_score']:<6} "
              f"{lead['grade']:<4} {status:<15} {lead['follow_up_date']:<12}")

    print()


def print_clients(status_filter: Optional[str] = None):
    """클라이언트 목록 출력."""
    data = load()
    clients = data["clients"]

    if status_filter:
        clients = [c for c in clients if c["status"] == status_filter]

    if not clients:
        print("클라이언트가 없습니다.")
        return

    print(f"\n총 {len(clients)}개의 클라이언트\n")
    print(f"{'ID':<6} {'브랜드':<20} {'패키지':<15} {'월료금':<12} {'상태':<10}")
    print("-" * 70)

    for client in clients:
        fee_str = _format_currency(client["monthly_fee"])
        brand_name = client['brand_name'][:20]
        package = client['package'][:15]
        status = client['status'][:10]
        print(f"{client['id']:<6} {brand_name:<20} {package:<15} "
              f"{fee_str:<12} {status:<10}")

    print()


def main():
    """CLI 인터페이스."""
    if len(sys.argv) < 2:
        print_dashboard()
        return

    command = sys.argv[1]

    if command == "dashboard":
        print_dashboard()

    elif command == "leads":
        status_filter = sys.argv[2] if len(sys.argv) > 2 else None
        print_leads(status_filter)

    elif command == "clients":
        status_filter = sys.argv[2] if len(sys.argv) > 2 else None
        print_clients(status_filter)

    elif command == "follow-ups":
        print("\n[이번 주 팔로업]\n")
        followups = get_follow_ups_this_week()
        if not followups:
            print("팔로업 예정이 없습니다.")
        else:
            for lead in followups:
                days = _days_until(lead["follow_up_date"])
                print(f"  {lead['follow_up_date']} (D-{days}) | {lead['brand_name']} | {lead['status']}")
        print()

    elif command == "renewals":
        print("\n[갱신 알림]\n")
        renewals = get_renewal_alerts()
        if not renewals:
            print("갱신 예정이 없습니다.")
        else:
            for client in renewals:
                days = _days_until(client["next_review"])
                print(f"  {client['next_review']} (D-{days}) | {client['brand_name']} | {client['package']}")
        print()

    elif command == "summary":
        summary = get_pipeline_summary()
        print("\n[파이프라인 요약]\n")
        print(f"총 리드: {summary['total_leads']}개")
        for status, count in summary["by_status"].items():
            print(f"  {status}: {count}개")
        print(f"\n운영중 클라이언트: {summary['active_clients']}개")
        print(f"월 매출: {_format_currency(summary['monthly_revenue'])}")
        print(f"예상 파이프라인: {_format_currency(summary['pipeline_value'])}\n")

    else:
        print(f"알 수 없는 명령어: {command}")
        print("\n사용법:")
        print("  dashboard    대시보드 출력")
        print("  leads        리드 목록 (선택: 상태 필터)")
        print("  clients      클라이언트 목록 (선택: 상태 필터)")
        print("  follow-ups   이번 주 팔로업")
        print("  renewals     갱신 알림")
        print("  summary      파이프라인 요약")


if __name__ == "__main__":
    main()

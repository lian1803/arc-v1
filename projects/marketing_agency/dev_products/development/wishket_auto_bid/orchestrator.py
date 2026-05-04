"""
위시켓 + 크몽 통합 자동입찰 CLI
사용법:
  python orchestrator.py monitor         # 전체 플랫폼 스캔 + 이메일
  python orchestrator.py monitor wishket # 위시켓만
  python orchestrator.py monitor kmong   # 크몽만
  python orchestrator.py status          # 처리 현황
  python orchestrator.py test            # 이메일 테스트
"""
import argparse
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / "cold_email_automation" / ".env")

from wishket_monitor import monitor as wishket_monitor, save_leads as save_wishket_leads
from kmong_monitor import monitor as kmong_monitor, save_leads as save_kmong_leads
from bid_generator import generate_batch
from notifier import send_notification

LEADS_FILE = Path(__file__).parent / "wishket_leads.jsonl"
SEEN_WISHKET = Path(__file__).parent / "seen_listings.jsonl"
SEEN_KMONG = Path(__file__).parent / "seen_kmong.jsonl"


def cmd_monitor(platform: str = "all"):
    all_new = []

    if platform in ("all", "wishket"):
        print("[위시켓] 스캔 시작...")
        w_new = wishket_monitor()
        print(f"  -> 새 의뢰: {len(w_new)}건")
        for item in w_new:
            item["platform"] = "위시켓"
        all_new.extend(w_new)
        if w_new:
            save_wishket_leads(w_new)

    if platform in ("all", "kmong"):
        print("[크몽] 스캔 시작...")
        k_new = kmong_monitor()
        print(f"  -> 새 의뢰: {len(k_new)}건")
        all_new.extend(k_new)
        if k_new:
            save_kmong_leads(k_new)

    if not all_new:
        print("새 의뢰글 없음.")
        return

    print(f"\n전체 {len(all_new)}건 발견. 입찰글 생성 중...")
    listings_with_bids = generate_batch(all_new)

    sent = send_notification(listings_with_bids)
    if not sent:
        print("[ERROR] 이메일 발송 실패. leads 파일에 저장됨.")


def cmd_status():
    def count_file(path):
        if not Path(path).exists():
            return 0
        return sum(1 for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip())

    w_seen = count_file(SEEN_WISHKET)
    k_seen = count_file(SEEN_KMONG)
    leads = count_file(LEADS_FILE)

    print(f"처리된 의뢰글: 위시켓 {w_seen}건 | 크몽 {k_seen}건")
    print(f"저장된 leads: {leads}건")

    if LEADS_FILE.exists():
        lines = [l for l in LEADS_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]
        recent = [json.loads(l) for l in lines[-5:]]
        print("\n최근 5건:")
        for item in recent:
            platform = item.get("platform", "?")
            print(f"  [{platform}] {item['title'][:45]} / {item.get('budget_text', '')}")


def cmd_test():
    test_items = [{
        "title": "테스트 - 쇼핑몰 주문 자동화",
        "category": "자동화",
        "budget_text": "100~150만",
        "platform": "테스트",
        "url": "https://www.wishket.com/project/test/",
        "bid_text": (
            "주문 관리 자동화 경험 있습니다.\n"
            "7일 납기 가능, 120만원 고정가.\n\n"
            "포트폴리오: https://github.com/lian1803\n"
            "30분 미팅으로 정확히 파악하겠습니다: https://calendly.com/lian1803"
        ),
    }]
    result = send_notification(test_items)
    print("테스트 발송 성공" if result else "테스트 발송 실패")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="통합 자동입찰 CLI")
    sub = parser.add_subparsers(dest="cmd")

    m_parser = sub.add_parser("monitor", help="전체 플랫폼 스캔")
    m_parser.add_argument("platform", nargs="?", default="all",
                          choices=["all", "wishket", "kmong"],
                          help="스캔할 플랫폼 (기본: all)")
    sub.add_parser("status", help="처리 현황")
    sub.add_parser("test", help="이메일 테스트")

    args = parser.parse_args()
    if args.cmd == "monitor":
        cmd_monitor(args.platform)
    elif args.cmd == "status":
        cmd_status()
    elif args.cmd == "test":
        cmd_test()
    else:
        parser.print_help()

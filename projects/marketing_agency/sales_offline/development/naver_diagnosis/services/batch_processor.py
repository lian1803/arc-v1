"""
배치 처리기
xlsx 파일에서 업체 목록 읽어서 순차 진단 큐 등록
"""
import asyncio
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
# 인메모리 배치 상태 저장소
# 서버 재시작 시 초기화됨 (MVP 수준)
# ─────────────────────────────────────────────────────────────
_batch_store: Dict[str, Dict[str, Any]] = {}


def get_batch_status(batch_id: str) -> Optional[Dict[str, Any]]:
    """배치 상태 조회."""
    return _batch_store.get(batch_id)


def list_batch_jobs() -> List[Dict[str, Any]]:
    """전체 배치 목록 반환 (최신순)."""
    jobs = list(_batch_store.values())
    jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jobs


# ─────────────────────────────────────────────────────────────
# xlsx 파싱
# ─────────────────────────────────────────────────────────────

BUSINESS_NAME_CANDIDATES = [
    "업체명", "상호명", "상호", "업체", "가게명", "가게", "이름", "name", "business_name",
    "업체 명", "상호 명",
]


def _detect_business_name_column(headers: List[str]) -> Optional[int]:
    """
    헤더 행에서 업체명 컬럼 인덱스 자동 감지.
    매칭 없으면 첫 번째 컬럼(0) 반환.
    """
    headers_lower = [str(h).strip().lower() for h in headers]
    for candidate in BUSINESS_NAME_CANDIDATES:
        if candidate.lower() in headers_lower:
            return headers_lower.index(candidate.lower())
    # 첫 번째 컬럼 기본값
    return 0


def parse_xlsx(file_path: str) -> List[str]:
    """
    xlsx 파일에서 업체명 목록 파싱.
    업체명 컬럼 자동 감지. 빈 값, 중복 제거.

    Returns:
        업체명 리스트
    """
    if not OPENPYXL_AVAILABLE:
        raise ImportError("openpyxl이 설치되어 있지 않습니다. pip install openpyxl")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return []

    # 첫 행을 헤더로 가정
    headers = [str(cell) if cell is not None else "" for cell in rows[0]]
    name_col_idx = _detect_business_name_column(headers)

    names = []
    seen = set()
    for row in rows[1:]:
        if not row or name_col_idx >= len(row):
            continue
        val = row[name_col_idx]
        if val is None:
            continue
        name = str(val).strip()
        if name and name not in seen:
            seen.add(name)
            names.append(name)

    return names


# ─────────────────────────────────────────────────────────────
# 배치 실행
# ─────────────────────────────────────────────────────────────

async def run_batch(
    batch_id: str,
    business_names: List[str],
    crawl_callback,
    delay_min: int = 5,
    delay_max: int = 10,
):
    """
    순차 진단 큐 실행.
    네이버 차단 방지: 랜덤 딜레이 + 연속 실패 감지 + 자동 일시정지.

    Args:
        batch_id: 배치 고유 ID
        business_names: 업체명 목록
        crawl_callback: async 함수 (business_name) -> history_id or None
        delay_min: 최소 딜레이 초 (기본 5초)
        delay_max: 최대 딜레이 초 (기본 10초)
    """
    import random

    total = len(business_names)
    consecutive_failures = 0
    current_delay_min = delay_min
    current_delay_max = delay_max

    _batch_store[batch_id].update({
        "status": "running",
        "total": total,
        "completed": 0,
        "failed": 0,
        "results": [],
        "started_at": datetime.utcnow().isoformat(),
    })

    for idx, name in enumerate(business_names):
        if _batch_store[batch_id].get("cancelled"):
            _batch_store[batch_id]["status"] = "cancelled"
            break

        try:
            history_id = await crawl_callback(name)
            _batch_store[batch_id]["results"].append({
                "business_name": name,
                "history_id": history_id,
                "success": history_id is not None,
            })
            if history_id is not None:
                _batch_store[batch_id]["completed"] += 1
                consecutive_failures = 0
                current_delay_min = delay_min
                current_delay_max = delay_max
            else:
                _batch_store[batch_id]["failed"] += 1
                consecutive_failures += 1
        except Exception as e:
            print(f"[Batch] {name} 진단 오류: {e}")
            _batch_store[batch_id]["results"].append({
                "business_name": name,
                "history_id": None,
                "success": False,
                "error": str(e),
            })
            _batch_store[batch_id]["failed"] += 1
            consecutive_failures += 1

        # 연속 실패 감지 → 차단 가능성 대응
        if consecutive_failures >= 3:
            print(f"[Batch] 연속 {consecutive_failures}회 실패 — 60초 대기 (차단 방지)")
            _batch_store[batch_id]["status"] = "paused_cooldown"
            await asyncio.sleep(60)
            _batch_store[batch_id]["status"] = "running"
            current_delay_min = delay_min * 2
            current_delay_max = delay_max * 2
            consecutive_failures = 0

        # 진행률 업데이트
        progress = int(((idx + 1) / total) * 100)
        _batch_store[batch_id]["progress"] = progress

        # 마지막 항목이 아니면 랜덤 딜레이
        if idx < total - 1:
            delay = random.uniform(current_delay_min, current_delay_max)
            await asyncio.sleep(delay)

    if _batch_store[batch_id].get("status") == "running":
        _batch_store[batch_id]["status"] = "done"
    _batch_store[batch_id]["finished_at"] = datetime.utcnow().isoformat()


def create_batch_job(file_path: str) -> Dict[str, Any]:
    """
    배치 잡 생성 및 등록.

    Returns:
        {
            "batch_id": str,
            "total": int,
            "business_names": [str],
            "status": "pending",
        }
    """
    business_names = parse_xlsx(file_path)
    if not business_names:
        raise ValueError("업체명 목록이 비어 있습니다. 파일 내용을 확인해주세요.")

    batch_id = str(uuid.uuid4())
    _batch_store[batch_id] = {
        "batch_id": batch_id,
        "file_path": file_path,
        "status": "pending",
        "total": len(business_names),
        "completed": 0,
        "failed": 0,
        "progress": 0,
        "results": [],
        "business_names": business_names,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "finished_at": None,
        "cancelled": False,
    }
    return _batch_store[batch_id]


def cancel_batch(batch_id: str) -> bool:
    """배치 취소 요청."""
    if batch_id in _batch_store:
        _batch_store[batch_id]["cancelled"] = True
        return True
    return False

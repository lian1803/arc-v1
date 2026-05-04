"""중복 업체 제거 및 병합"""
import logging
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


def _normalize_name(name: str) -> str:
    """업체명 정규화: 공백/특수문자 제거, 소문자 변환"""
    normalized = re.sub(r'[\s\-_\.\(\)\[\]·•]', '', name).lower()
    return normalized


def _address_prefix(address: str, length: int = 10) -> str:
    """주소 앞 N자 추출 (공백 제거 후)"""
    if not address:
        return ""
    return re.sub(r'\s+', '', address)[:length]


def _merge_records(base: dict, other: dict) -> dict:
    """
    두 레코드 병합. base를 기준으로 other의 정보로 보완.
    더 많은 정보가 있는 쪽 값을 우선.
    """
    merged = dict(base)

    # 문자열 필드: 비어있으면 other 값으로 채움
    string_fields = ["phone", "insta_url", "naver_place_url", "daangn_url", "raw_address"]
    for field in string_fields:
        if not merged.get(field) and other.get(field):
            merged[field] = other[field]

    # phone_status: "확인"이 "번호미확인"보다 우선
    if other.get("phone_status") == "확인" and merged.get("phone_status") != "확인":
        merged["phone_status"] = "확인"
        if other.get("phone"):
            merged["phone"] = other["phone"]

    # verify_status: "확인됨" > "미확인" > "폐업의심" 우선순위
    status_priority = {"확인됨": 3, "미확인": 2, "폐업의심": 1}
    current_priority = status_priority.get(merged.get("verify_status", "미확인"), 2)
    other_priority = status_priority.get(other.get("verify_status", "미확인"), 2)
    if other_priority > current_priority:
        merged["verify_status"] = other["verify_status"]
        if other.get("naver_place_url"):
            merged["naver_place_url"] = other["naver_place_url"]

    # sources: 출처 합치기 (중복 제거)
    base_sources = set(s.strip() for s in (merged.get("sources") or merged.get("source", "")).split(",") if s.strip())
    other_sources = set(s.strip() for s in (other.get("sources") or other.get("source", "")).split(",") if s.strip())
    merged_sources = base_sources | other_sources
    merged["sources"] = ",".join(sorted(merged_sources))

    return merged


def _score_record(record: dict) -> int:
    """레코드 정보량 점수 계산 (병합 기준 선택용)"""
    score = 0
    if record.get("phone"):
        score += 3
    if record.get("insta_url"):
        score += 2
    if record.get("naver_place_url"):
        score += 2
    if record.get("raw_address"):
        score += 1
    if record.get("daangn_url"):
        score += 1
    if record.get("verify_status") == "확인됨":
        score += 2
    return score


def deduplicate(records: list[dict]) -> list[dict]:
    """
    중복 업체 병합.

    병합 기준 (우선순위 순):
    1. 완전히 같은 업체명(정규화) + 같은 전화번호 → 병합
    2. 완전히 같은 업체명(정규화) + 주소 앞 10자 일치 → 병합
    3. 같은 전화번호 (010 번호만, 비어있으면 제외) → 병합

    병합 시: 정보량이 많은 레코드를 base로, 나머지로 보완.
    """
    if not records:
        return records

    original_count = len(records)

    # 그룹핑용 딕셔너리
    # key: 대표 식별자 → [인덱스 목록]
    groups: dict[str, list[int]] = defaultdict(list)
    assigned: dict[int, str] = {}  # 인덱스 → 그룹키

    def assign(idx: int, key: str):
        if idx in assigned:
            # 이미 다른 그룹에 있으면 그룹 병합
            old_key = assigned[idx]
            if old_key != key:
                # old_key 그룹의 모든 인덱스를 key 그룹으로 이동
                for old_idx in groups[old_key]:
                    groups[key].append(old_idx)
                    assigned[old_idx] = key
                del groups[old_key]
        else:
            groups[key].append(idx)
            assigned[idx] = key

    # 패스 1: 업체명 정규화 + 전화번호로 그룹핑
    name_phone_map: dict[str, int] = {}
    for i, record in enumerate(records):
        name = _normalize_name(record.get("name", ""))
        phone = record.get("phone", "")

        if name and phone:
            key = f"np:{name}:{phone}"
            if key in name_phone_map:
                existing_key = assigned.get(name_phone_map[key], f"solo:{name_phone_map[key]}")
                assign(i, existing_key)
                assign(name_phone_map[key], existing_key)
            else:
                name_phone_map[key] = i
                assign(i, f"np:{name}:{phone}")

    # 패스 2: 업체명 정규화 + 주소 앞 10자로 그룹핑
    name_addr_map: dict[str, int] = {}
    for i, record in enumerate(records):
        name = _normalize_name(record.get("name", ""))
        addr_prefix = _address_prefix(record.get("raw_address", ""))

        if name and addr_prefix:
            key = f"na:{name}:{addr_prefix}"
            if key in name_addr_map:
                j = name_addr_map[key]
                existing_key_i = assigned.get(i, f"solo:{i}")
                existing_key_j = assigned.get(j, f"solo:{j}")
                if existing_key_i != existing_key_j:
                    # 두 그룹 병합
                    merge_key = existing_key_j
                    for idx in list(groups.get(existing_key_i, [i])):
                        if idx not in groups.get(merge_key, []):
                            groups[merge_key].append(idx)
                        assigned[idx] = merge_key
                    if existing_key_i in groups:
                        del groups[existing_key_i]
            else:
                name_addr_map[key] = i
                if i not in assigned:
                    assign(i, f"na:{name}:{addr_prefix}")

    # 패스 3: 전화번호만으로 그룹핑 (010 번호만)
    phone_map: dict[str, int] = {}
    for i, record in enumerate(records):
        phone = record.get("phone", "")
        if phone and phone.startswith("010"):
            if phone in phone_map:
                j = phone_map[phone]
                existing_key_i = assigned.get(i, f"solo:{i}")
                existing_key_j = assigned.get(j, f"solo:{j}")
                if existing_key_i != existing_key_j:
                    merge_key = existing_key_j
                    for idx in list(groups.get(existing_key_i, [i])):
                        if idx not in groups.get(merge_key, []):
                            groups[merge_key].append(idx)
                        assigned[idx] = merge_key
                    if existing_key_i in groups:
                        del groups[existing_key_i]
            else:
                phone_map[phone] = i
                if i not in assigned:
                    assign(i, f"phone:{phone}")

    # 아직 그룹 미배정 레코드 단독 처리
    for i in range(len(records)):
        if i not in assigned:
            assign(i, f"solo:{i}")

    # 각 그룹 병합
    merged_results: list[dict] = []
    processed_keys: set[str] = set()

    for i, record in enumerate(records):
        group_key = assigned.get(i)
        if group_key is None or group_key in processed_keys:
            continue

        group_indices = groups[group_key]
        processed_keys.add(group_key)

        if len(group_indices) == 1:
            merged_results.append(dict(record))
            continue

        # 그룹 내 레코드 정보량 점수 기준 정렬 (높은 순)
        group_records = [records[idx] for idx in group_indices]
        group_records.sort(key=_score_record, reverse=True)

        base = dict(group_records[0])
        for other in group_records[1:]:
            base = _merge_records(base, other)

        merged_results.append(base)
        logger.debug(
            "deduplicator: %d건 병합 — %s",
            len(group_indices), base.get("name", ""),
        )

    final_count = len(merged_results)
    removed_count = original_count - final_count
    logger.info(
        "deduplicator: %d건 → %d건 (중복 %d건 제거)",
        original_count, final_count, removed_count,
    )
    return merged_results

"""010 번호 필터링 및 정규화"""
import logging
import re

try:
    import phonenumbers
    HAS_PHONENUMBERS = True
except ImportError:
    HAS_PHONENUMBERS = False

logger = logging.getLogger(__name__)

# 010으로 시작하는 11자리 숫자 패턴 (하이픈 포함/제외 모두)
MOBILE_010_PATTERN = re.compile(r'^010[-\s]?\d{4}[-\s]?\d{4}$')
# 유선전화 패턴 (02, 031~064 등)
LANDLINE_PATTERN = re.compile(r'^0(?:2|3[1-9]|4[1-9]|5[1-9]|6[1-9])[-\s]?\d{3,4}[-\s]?\d{4}$')


def normalize_phone(phone: str) -> str:
    """
    전화번호를 표준 하이픈 형식으로 정규화.
    - "01012345678"     -> "010-1234-5678"
    - "010 1234 5678"   -> "010-1234-5678"
    - "010-1234-5678"   -> "010-1234-5678" (이미 정규화됨)
    - "+821012345678"   -> "010-1234-5678"
    """
    if not phone:
        return phone

    # phonenumbers 라이브러리 사용 가능 시 우선 활용
    if HAS_PHONENUMBERS:
        try:
            parsed = phonenumbers.parse(phone, "KR")
            if phonenumbers.is_valid_number(parsed):
                national = phonenumbers.format_number(
                    parsed, phonenumbers.PhoneNumberFormat.NATIONAL
                )
                # "010-1234-5678" 형식으로 반환됨
                return national
        except Exception:
            pass

    # 숫자만 추출
    digits = re.sub(r"[^\d]", "", phone)

    # 국제번호 +82 제거
    if digits.startswith("82") and len(digits) >= 11:
        digits = "0" + digits[2:]

    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    elif len(digits) == 10 and digits.startswith("010"):
        # 010-xxx-xxxx 형식 (8자리 국번)
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

    # 정규화 불가 시 원본 반환
    return phone


def is_mobile_010(phone: str) -> bool:
    """010으로 시작하는 11자리 번호인지 확인"""
    if not phone:
        return False
    normalized = normalize_phone(phone)
    return bool(MOBILE_010_PATTERN.match(normalized))


def is_landline(phone: str) -> bool:
    """유선전화 번호인지 확인"""
    if not phone:
        return False
    digits = re.sub(r"[^\d]", "", phone)
    # 02 (서울), 031~064 (각 지역)
    return bool(re.match(r'^0(?:2\d{7,8}|[3-6]\d{8,9})$', digits))


def filter_phones(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    010 번호 기준 필터링.

    반환: (통과한 레코드 list, 제거된 레코드 list)

    처리 규칙:
    - 010으로 시작하는 11자리 번호 -> phone 정규화 후 통과 (phone_status="확인")
    - 전화번호 없음 -> phone_status="번호미확인" 유지, 통과 (삭제 안 함)
    - 031/032/02 등 유선번호 -> phone 비우고 phone_status="번호미확인" 으로 변경, 통과
    - 010이지만 자릿수 이상한 번호 -> phone 비우고 phone_status="번호미확인", 통과
    """
    passed: list[dict] = []
    removed: list[dict] = []

    for record in records:
        phone = record.get("phone", "") or ""
        phone = phone.strip()

        if not phone:
            # 번호 없음 — 통과 (phone_status 유지 또는 설정)
            record["phone_status"] = "번호미확인"
            passed.append(record)
            continue

        if is_mobile_010(phone):
            # 010 모바일 번호 — 정규화 후 통과
            record["phone"] = normalize_phone(phone)
            record["phone_status"] = "확인"
            passed.append(record)
            logger.debug("phone_filter: 통과 — %s", record["phone"])
            continue

        if is_landline(phone):
            # 유선전화 — phone 비우고 통과
            logger.debug("phone_filter: 유선번호 제거 — %s (%s)", phone, record.get("name", ""))
            record["phone"] = ""
            record["phone_status"] = "번호미확인"
            passed.append(record)
            continue

        # 010으로 시작하지만 형식 이상하거나 알 수 없는 번호
        digits = re.sub(r"[^\d]", "", phone)
        if digits.startswith("010"):
            # 010인데 자릿수 문제 — 비우고 통과
            logger.debug("phone_filter: 010 형식 불량 — %s", phone)
            record["phone"] = ""
            record["phone_status"] = "번호미확인"
            passed.append(record)
        else:
            # 완전히 알 수 없는 번호 형식 — 비우고 통과
            logger.debug("phone_filter: 알 수 없는 번호 형식 — %s", phone)
            record["phone"] = ""
            record["phone_status"] = "번호미확인"
            passed.append(record)

    logger.info(
        "phone_filter: 전체 %d건 처리 — 통과 %d건 / 제거 %d건",
        len(records), len(passed), len(removed),
    )
    return passed, removed

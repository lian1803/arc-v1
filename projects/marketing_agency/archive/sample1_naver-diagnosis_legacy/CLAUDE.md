# naver-diagnosis — 백엔드 API 전용

## ⚠️ 이 폴더의 역할
**백엔드 API 엔진만.** 프론트엔드 없음.

| 구분 | 위치 | 포트 |
|------|------|------|
| **실제 UI (진짜 프론트)** | `소상공인_영업툴/sales_crm/app.py` | 5000 |
| 이 폴더 (API만) | `naver-diagnosis/` | 8000 |

## ⛔ 절대 금지
- `naver-diagnosis/templates/` 수정 금지 — 실제로 안 쓰는 코드
- `naver-diagnosis/static/` UI 작업 금지 — 사용자는 sales_crm을 씀
- 010 처리, 배치 로직 새로 짜기 금지 → sales_crm/app.py에 이미 있음

## 새 기능 착수 전 grep 먼저

```bash
# 비슷한 기능 있는지 먼저 확인 (전체 스캔 대신 키워드만)
grep -r "기능키워드" "../소상공인_영업툴/sales_crm/" --include="*.py" -l
grep -r "기능키워드" "../../../../../../company/" --include="*.py" -l
```

## 이 폴더에서 할 수 있는 작업
- `services/` — 크롤링, 점수 계산, 메시지 생성 로직
- `routers/` — FastAPI 엔드포인트
- `models.py`, `database.py` — DB 스키마
- `config/industry_weights.py` — 업종별 가중치

## sales_crm 연결 구조
sales_crm이 `http://localhost:8000` 으로 이 API 호출.
새 기능은 → 여기에 API 엔드포인트 추가 → sales_crm에서 호출하는 방식.

## 서버 시작
`C:\Users\lian1\Desktop\CRM서버시작.bat` — sales_crm(5000) 시작
naver-diagnosis는 `uvicorn main:app --port 8000` 별도 실행

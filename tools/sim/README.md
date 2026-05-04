# tools/sim — 빌드 끝 시뮬 (페르소나 손으로 써보기)

빌드 후 ARC가 ICP 손인 척 직접 클릭해서 회원가입→첫 가치→결제까지 작동하는지 검증.
PASS = 빌드 끝. FAIL = 재빌드.

**새 framework 만들지 X.** luna 에서 invoice-snap 빌드 때 실제로 작성·작동시킨 도구를 reference로 보존. 다음 프로젝트는 이걸 복사·변형해서 써.

## reference/invoice_snap/ — 5개 파일 (Playwright 기반)

| 파일 | 무엇을 함 |
|---|---|
| `invoice_snap_browser_test.py` | headless Chromium 띄워 진짜 파일 업로드 → 큐 처리 → CSV 다운로드 → 스키마 검증 |
| `invoice_snap_mobile_test.py` | iPhone 14 viewport 에뮬, 가로스크롤 / hero / 배너 / dropzone 가시성 검증 |
| `invoice_snap_reality_test.py` | Lian 실제 Gemini 키로 end-to-end OCR 정확도 검증 (vendor / date / amount / VAT) |
| `invoice_snap_test_lib.py` | 공통 헬퍼 (call_gemini_vision / generate_csv / validate_csv) |
| `invoice_snap_variant_gen.py` | 한국 세금계산서 / 영수증 PNG 합성기 (테스트 입력) |

## reference/smoke_checks/ — luna 시스템 자체 smoke

ARC 자체 sanity check 용 (live_and_spawn / archiver / indices / state). 즉시 carry over X. 필요할 때 참조.

## 새 프로젝트에 쓰는 법 (Pieter Levels 식 1인 패턴)

1. `tools/sim/{project_name}/` 폴더 만들기
2. invoice_snap_*_test.py 중 가장 가까운 거 1개 복사 → 변형
3. 하드코딩된 URL / 검증 항목만 새 프로젝트에 맞게 교체
4. 새 framework 추출 X (또 luna 됨). 사례 → 사례.

## 의존성

- Python 3.11+
- `pip install playwright && playwright install chromium`
- 일부는 .env (GEMINI_API_KEY 등) 필요

## 출처

luna/tools/ 에서 carry over (2026-05-03). 원본 commit 이력은 luna 보존.

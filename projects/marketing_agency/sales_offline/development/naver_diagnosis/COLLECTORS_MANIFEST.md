# Sales_Offline 수집기 매니페스트

> 1번세션 (오프라인) 다음 세션 시작점. "1세션 오프라인" trigger → 이 파일 read first.
> 20 수집기 + 1 orchestrator. 양주/북부수도권 010 lead 수집 시스템.

## 최신 통합 unique 010 (2026-04-29 session 31 close)
- **경기북부 6 region cross-dedupe = 9,517**
- 전체 lead_db 44 도시 cross-dedupe = 58,894+

## 20 수집기

| # | 수집기 | source | 010 추출 방식 |
|---|---|---|---|
| 1 | collect_naver_map.py | 네이버 지도 | place 정보 |
| 2 | collect_naver_map_api.py | 네이버 지도 API | place |
| 3 | collect_naver_blog.py | 네이버 블로그 | 본문 010 |
| 4 | collect_naver_cafe.py | 네이버 카페 | 본문 010 |
| 5 | collect_naver_kin.py | 네이버 지식인 | 본문 |
| 6 | collect_naver_booking.py | 네이버 예약 | place |
| 7 | collect_kakao_map.py | 카카오맵 | JSON intercept |
| 8 | collect_google_010.py | Google 검색 | 검색 결과 |
| 9 | collect_instagram_010.py | 인스타그램 | bio/post |
| 10 | collect_bing_maps.py | Bing Maps | place |
| 11-17 | collect_daangn_*.py (7) | 당근마켓 | 동별/직접/구글/profile |
| **18** | **collect_daum_search.py** 🆕 | **Daum 검색** | **010 keyword 검색 (session 31 박음, +127 unique)** |
| 19 | merge_north_metro.py | 통합 + dedupe | merge by (이름+phone) |
| 20 | merge_yangju_db.py | 양주 통합 | merge |

## 공통 spec (모든 수집기)
- REGIONS = `["남양주", "양주", "포천", "의정부", "동두천", "가평"]` (6 region = 경기북부)
- KEYWORDS = `["미용실", "카페", "음식점", "학원", "헬스장", "네일", "피부관리", "고깃집", "치킨", "부동산"]` (10 업종)
- 출력: `lead_db/{prefix}_{TS}.xlsx` + `desktop/오프라인진단/{prefix}_{TS}.xlsx`
- dedupe: digit-only 010 → set

## 양주 진단 (2단계 = 데이터 풀 긁기)
- `run_one_to_md.py [업체명]` — 1 가게 진단 → `desktop/오프라인진단/{biz}_진단_{TS}.md`
- `run_batch_test.py` — `BATCH_SIZE=100` 가게 batch (양주 첫 100 자동)
- 결과 stat (양주 100 batch 2026-04-29): **B 78 / C 13 / D 9 / 평균 63.1 / 평균 손실 675명**
- ⚠️ D 등급 8% (점수 < 30) = 데이터 0 가게 = **발송 단계 거름 의무** (carry, §5)

## 새 source 박는 template
1. `collect_kakao_map.py` 또는 `collect_daum_search.py` 패턴 모방
2. 양주 5kw × 5업종 sample test (100+ hit) → unique 010 ≥ 10 (10% 유효율) PASS
3. `lead_db/` + `desktop/오프라인진단/` 둘 다 출력
4. 이 manifest 에 entry 추가 (#21 등)

## 다음 세션 "1세션 오프라인" 트리거 시
1. 이 manifest read
2. `sales_offline/CLAUDE.md` read (ICP / 가격 / 5 업종 Pain)
3. `NEXT_SESSION.md` 1번세션 carry 확인
4. Lian 다음 액션 명령 대기 OR 자동 진행:
   - `python run_all_collectors.py` — 20 수집기 sequential run
   - `python run_batch_test.py` — 양주 batch 재개
   - 수집기 다른 도시 적용 (REGIONS 변수만 변경 = scalable)

## 외부 API key
- ✅ `DATAGO_API_KEY` (박힘, naver_diagnosis/.env) — apis.data.go.kr 소상공인 상가정보. **010 필드 X = lookup 용 (65만 상가, 상호+주소+업종+사업자번호)**
- 🔴 식약처 OpenAPI key — Lian 5분 web 폼 (https://openapi.foodsafetykorea.go.kr)
- 🔴 LOCALDATA — SSL/redirect 차단, sandbox 못 hit
- ✅ NAVER_AD_* (검색광고 API, 키워드 검색량) 박힘

## 1번세션 → 다음 세션 carry
- §2 silent-fail (`run_one_to_md.py` L357/L401 — 검색량/브랜드 try-except print swallow). §9 grandfather 1946 LOC split 트리거 회피로 carry.
- §5 D등급 발송 단계 거름 (진단 결과 발송 전 photo 0 / review 0 / blog 0 가게 분기).
- merge_*.py archive 로직 0 (drift) — 다음 collect 후 옛 통합 archive 자동화 fix.
- sub-agent 영어 keyword 결함 (memory `feedback_subagent_english_keyword.md` 신규).
- §17 위반 1회 (어제 DATAGO_API_KEY 인계 누락, 서연이 "key 없다" 잘못 보고).
- 3단계 = ? Lian 정의 대기 ("리뷰" = 가게 별점 마케팅 / 진단 검수 / 영업 멘트 검수 — 미정).

## D 옵션 (오프라인 다음 step, session 27 carry 미해소)
- 옵션 1: 2-4차 메시지 분기 자동화
- 옵션 2: Lian 직접 양주 1-2 가게 실 진단 + 영업 시도 (서연 추천)
- 옵션 3: 멈춤 + lead magnet 으로 inbound 전환

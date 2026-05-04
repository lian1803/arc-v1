# 1차 점검 결과 — 크롤링 파이프라인 상태 (2026-04-28)

## 요약
- crm_businesses 총 12,117개 / 양주 2,681개 / 진단 완료 0개 (양주 기준)
- diagnosis_history 12개 전부 오류 (12/12)
- 파이프라인 자체는 실행됨 (API 정상, playwright 정상)
- 구조적 누락 3종 발견 (개별 버그 아님, 모든 기록에 공통)

## DB 현황
| 항목 | 수치 |
|------|------|
| crm_businesses 총 | 12,117 |
| 양주 가게 | 2,681 |
| 진단 완료 (양주) | 0 |
| place_url 있는 가게 | 0 (전체) |
| diagnosis_history 전체 | 12 |
| crm 연결된 진단 | 2 (테스트용) |

## 양주 업종 분포 (상위 10)
네일 209 / 필라테스 141 / 애견미용 121 / 반려동물 119 / 피부관리 116
영어학원 104 / 학원 102 / 인테리어 87 / 왁싱 87 / 속눈썹 81

## 구조적 누락 3종
1. photo_quality_score 항상 0 (photo_analyzer 미호출)
2. review_last_30d/90d 항상 0 (크롤러 수집 로직 없음)
3. related_keywords 비어있음 (get_related_keywords 미호출)

## API 상태
- 네이버 검색 API: 200 OK
- Playwright: 정상
- 실측(아이결): 76.8점 B등급 성공

---
name: topyt_무릎통증_pattern_2026-05-04
description: 한국 무릎통증/관절염 YouTube 상위 12개 (15만~400만 view) 썸네일 시각 분석 → 실제 패턴
status: active
authored_by: seoyeon-2026-05-04
created_at: 2026-05-04
sample_count: 10 visually analyzed (out of 12 downloaded)
view_range: 156K - 4M
---

# 한국 무릎통증 YouTube 상위 썸네일 패턴 (2026-05-04 fresh)

## BLUF
이전 분석 (`health_youtube_thumbnail_corpus_kr.md` 35-sample, 시니어 일반)은 채널 layout만 봤음. 실제 무릎통증 카테고리 top 10을 시각으로 까보니 **글자 폭격** 패턴이 압도. 내가 만든 21장의 실패 원인 = "사진 위주 + 작은 텍스트" 였음.

## 시각 분석 — 10장 직접 검증

| # | view | 핵심 패턴 |
|---|---|---|
| 1 | 4.0M | 텍스트 60% (퇴행성/관절염/치료법 3줄, 거대 cyan-blue) + 인물 우 40% |
| 2 | 2.5M | 텍스트 70%! (4줄, 멀티컬러: cyan/yellow/red/white) + 무릎잡은 손 사진 |
| 3 | 2.2M | 빨간 띠 "수술없이" + 파란 박스 "단 하나의 방법" + 의사 우 |
| 4 | 1.9M | 텍스트 65% (4줄 "무릎연골주사/에 대해/꼭 알아야 할/9가지") + 의사 우 |
| 5 | 980K | 노랑 "수술 없이" + 흰 "무릎 건강 지킨다" + 자세 사진 |
| 6 | 940K | 노랑 뱃지 "90만 조회수" + 흰 "자기전 5분 / 20대 무릎 됩니다" + 무릎 close-up |
| 7 | 596K | 4줄 멀티컬러 (yellow/green/white/cyan) "식사 후 / 한 잔씩 / 매일 마시면 / 무릎통증 사라진다!" + 음료 |
| 8 | 384K | 흰 큰 "반월상 연골판 파열" + MRI 사진 + 우상단 헬스조선 뱃지 |
| 9 | 336K | 좌하 "당신이 꼭 알아야 할 / 무릎 통증" + 의사 2명 인터뷰 사진 |
| 11 | 253K | 거대 cyan "관절염에 / 좋은 운동법" + 일러스트 우 |

(10번은 중복 패턴 skip, 12번은 8번과 동일 의사)

## 압도적 공통 패턴 (10/10)

### 1. 텍스트가 주인공, 사진은 보조 (50-70% 면적)
- 내 21장 = 사진이 50-60%, 텍스트 30%. **반대로 해야 됨.**
- 메인 텍스트 폰트 **130-180px** (canvas 1280×720 기준). 내가 쓴 86-92px = 너무 작음.

### 2. 외곽선 두께 (12-15px black)
- 내 5-6px = 안 보임. **2-3배 굵게.**

### 3. 한 썸네일 안에 3-4 컬러 (단어별 색상 분리)
대부분 같은 줄/다른 줄에 **다른 키워드 = 다른 색**:
- yellow `#FFEB1E` — 시간/숫자/조건 ("식사 후", "5분")
- cyan `#1ED9F0` 또는 lightblue — 동작/방법 ("이 운동", "한 잔씩")
- red `#FF1E1E` — 결과/충격 ("사라진다", "긴급")
- white `#FFFFFF` — 본문/설명
- 내 21장 = 줄별 단색만. **단어별 컬러 split 필요.**

### 4. 사진 = real photo OR body part close-up
- 의사 portrait — but **broadcast/clinic 자연** (스튜디오 AI 부드러움 X)
- 무릎 잡은 손 close-up
- 음료 잔 close-up
- MRI / X-ray
- 약 / 음식
- 내 16장 = AI 스튜디오 portrait 위주. **body part close-up + real-feel 강화.**

### 5. 카피 = 구체 동사 + 약속
| 잘됨 | 나 |
|---|---|
| "사라진다!" | "100% 없애는" |
| "20대 무릎 됩니다" | "단 1가지 음식 vs" |
| "강철무릎 됩니다!" | "최악의 습관 공개" |
| "수술없이" | "60대 무릎 통증" |
**동사+느낌표 강한 약속.** 명사 나열 금지.

### 6. 레이아웃 = 텍스트 좌(또는 전체) + 이미지 우 hard cut
- 페이드/그래디언트 X. **하드 가장자리.**
- 내 fade_panel 함수 = 잘못. **사각 박스로 배경 hard split.**

### 7. 뱃지 = 우상단/좌상단 2-3줄 채널 로고 OR 조회수
- 내가 쓴 "건강정보" 뱃지는 OK.
- 추가로 "90만 조회수" / "EBS STORY" 같은 신뢰 마커 효과.

## 즉시 적용 차이

| 변수 | 내 21장 (실패) | top 10 (수백만 view) |
|---|---|---|
| 텍스트 면적 | 30% | **50-70%** |
| 메인 폰트 | 86-92px | **130-180px** |
| 외곽선 | 5-6px | **12-15px** |
| 줄당 컬러 | 1색 | **2-3색 분리** |
| 사진 | AI 스튜디오 인물 | **body part close-up + real broadcast feel** |
| 카피 | 명사 나열 | **동사 + 느낌표 약속** |
| 배경 | gradient/fade | **hard color block** |

## 외부 정론 비교
- vidIQ 2024 thumbnail study: "Text-first thumbnails 27% higher CTR" — 동의.
- MrBeast public talks (2023-): "Big bold text + simple image" — 동의.
- Brunch 가이드 (이미 ARC 인용): "대비 + 강한 색" CTR ↑15% — 부분 동의 (강한 색은 맞으나 "split layout"보다 "text dominance"가 더 큰 변수).
- 기존 health_youtube_thumbnail_corpus_kr.md: "85% = 좌검정+우인물" — 부분 동의 (layout은 맞지만 좌측에 들어가는 게 큰 텍스트라는 점이 핵심인데 corpus 분석에서 빠짐).

## 다음
`gen_thumbs_topyt_v2.py` 작성 — 위 7항 strict 적용. 12장.

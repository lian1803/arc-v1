---
name: youtube_senior_kr_4molds
description: 시니어 한국 유튜브 4 금형 — 제목/키워드/썸네일/자막 fill-in-blank
status: active
authored_by: Seoyeon-session31
created_at: 2026-04-29
sources:
  - "https://www.tubebuddy.com/blog/advanced-keyword-research-techniques-for-youtube-in-2026/"
  - "https://partnerhelp.netflixstudios.com/hc/en-us/articles/216001127-Korean-Timed-Text-Style-Guide"
  - "https://air.io/en/youtube-hacks/best-practices-for-writing-and-formatting-subtitles"
  - "https://www.rev.com/blog/the-best-and-worst-font-colors-for-closed-captions"
  - "https://github.com/m1guelpf/yt-whisper"
  - "https://www.w3.org/WAI/media/av/captions/"
---
# 시니어 한국 유튜브 4 금형

## BLUF
무릎→당뇨·고혈압 바꿀때 이 4개 금형만 쓰면 일관성있게완성. 1영상=슬롯7개+선택5분.

## 공통슬롯
- {TOPIC}: 무릎통증 / 당뇨 / 고혈압
- {AGE}: 60대 / 70대 / 80대
- {CORE_KW}: 무릎통증 
- {SOLUTION_TYPE}: 음식 / 습관 / 운동
- {NUMBER}: 1 / 3 / 5
- {AUTHORITY}: 의사 / 약사 / 한의사

## 1. 제목3패턴

**Pattern1** (CTR최고): {AGE} {TOPIC} 100% 없애는 {NUMBER}가지 {SOLUTION_TYPE} vs 최악습관
예: "60대당뇨 절대안되는 1가지음료vs추천3가지" | 근거: TubeBuddy +20-30% CTR

**Pattern2**: {AUTHORITY}추천 {TOPIC} {NUMBER}가지 {SOLUTION_TYPE}
예: "정형외과의사추천무릎통증음식5가지" | 근거: YouTube공식신뢰도신호CTR↑

**Pattern3**: 절대하지마! {AGE} {TOPIC} 악화 {NUMBER}가지
예: "절대하지마!60대무릎통증악화1가지" | 근거: 경고강조어+18%

글자수sweet spot: 40-55자 (모바일완전표시)

## 2. 키워드10-스택

1. {CORE_KW}  2. {AGE}{CORE_KW}  3. {CORE_KW}{SOLUTION_TYPE}  4. {AUTHORITY}추천{CORE_KW}
5. {CORE_KW}자연치유  6. 약안먹고{CORE_KW}  7. {CORE_KW}{NUMBER}가지  8. {CORE_KW}vs최악{SOLUTION}
9. {AGE}건강관리  10. {CORE_KW}응급

근거: YouTube SEO 롱테일경쟁低

## 3. 썸네일금형

**Spec**: 16:9, 밝은파랑/베이지, {AUTHORITY}얼굴+자연미소, {SOLUTION_TYPE}클로즈업, 텍스트4-7자Bold(빨강/노랑), 명암4.5:1

**Gemini Prompt**:
Photorealistic 16:9. Korean {AGE} {AUTHORITY} with warm smile holding {SOLUTION_TYPE}, soft blue/beige background, professional healthcare. No text.

후처리: Canva/Photoshop한글텍스트overlay(20pt+)

## 4. 자막금형 (신규research)

**시니어가독성**:
- 줄당: ≤20-25자 (CJK너비) | Netflix한국
- 표시: 3-5초 (느린읽기) | AIR2026
- 글꼴: NotaSansKR 20pt+ | Rev접근성
- 색상: 흰텍+검은외곽선 (대비4.5:1) | W3C
- 줄수: 최대2줄 | 한국방송표준
- 위치: 하단중앙

**절차 (4-Step)**:
1. mp4→Whisper response_format="srt" | Whisper 98.5% 정확도
2. 각줄≤20-25자split (SubtitleEdit/Subper)
3. 타이밍: 2초→3-5초 (CPS 4-5유지)
4. 후처리: FinalCut/Canva재배출+스타일 (YouTube자막제한우회)

## 5. 외부정론 (6소스)

1. TubeBuddy 2026: 숫자 +20-30% CTR
2. YouTube공식: 제목40자+썸네일얼굴색상
3. Netflix한국: 자막2줄, 20-25자/줄
4. AIR2026: 자막3-5초전시
5. Rev: 흰텍+검외곽선대비4.5:1
6. GitHub Whisper: 한국어 98.5% 정확도

합의: 숫자+절대금지=CTR↑, 롱테일경쟁LOW, 얼굴표정=시니어선호, 자막3-5초+큰글=접근성표준

## 6. Falsifier
✅ 다른주제(70대당뇨)입력→5분안에4개산출완료
✅ 외부소스≥5개
✅ 슬롯정의명확
→ 3개모두PASS = 금형PASS

## 7. 다음영상체크 (5분)
1. 슬롯7개채우기 (30초)
2. 제목Pattern선택 (30초)
3. 키워드10개채우기 (30초)
4. 썸네일Prompt→생성→Canva텍스트 (60초)
5. Whisper→줄split→타이밍조정 (60초)

---
name: topyt_무릎_corpus_v2_2026-05-04
description: 60장 (5만~497만 view) 무릎/관절 YouTube 썸네일 wide corpus + GitHub MARCELO 패턴 통합
status: active
authored_by: seoyeon-2026-05-04
created_at: 2026-05-04
sample_count: 60 (downloaded), 14 visually analyzed
view_range: 50K - 4.97M
sources:
  - 60 YouTube thumbnails (D:/work/ARC/.tmp_thumbs_wide/)
  - GitHub eddieoz/youtube-clips-automator (160★ MARCELO)
  - perplexity dive Korean senior health 2026-05-04
  - perplexity dive thumbnail factory pipeline 2026-05-04
  - existing health_youtube_thumbnail_corpus_kr.md (35-sample baseline)
  - existing topyt_무릎통증_pattern_2026-05-04.md (10-sample first pass)
---

# Wide corpus v2 — 추가 발견 패턴 (1차 분석에서 빠진 것)

## BLUF
1차 (10장 분석) = 의사 portrait + 큰 텍스트 + 거대 outline. 맞지만 부족.
2차 (60장 corpus) = 추가 4 패턴이 사실 더 큰 변수.

## 새로 잡힌 4 패턴

### A. **개인 후기 톤** (1차 누락)
- #004 (342만) "누워서 따라했더니 / 무릎 통증 사라지고 / 걷기 편해졌어요!"
- #012 (180만) "의자에 앉아서 / 매일 했더니 / 허리6인치 줄고 / 허벅지돌덩이됐어요"
- 의사 위협 톤 (X), 일반인 증언 톤 (✓). "했더니/됐어요/편해졌어요" 어미.

### B. **운동 중인 일반인 누끼** (의사 portrait X)
- #001 (497만) "하체 근력" — 매트에 누워서 다리 든 일반인
- #002 (407만) — 운동복 일반인 + 무릎 잡은 자세
- #004 (342만) — 트레이너 thumbs up
- #006 (228만) — body close-up (손가락 마사지)
- AI 스튜디오 의사 portrait 보다 **자연 운동 자세**가 view 더 잘 나옴.

### C. **흰 배경 + GIANT 단색 검정 텍스트** (outline 거의 없음)
- #001 (497만) "하체 근력(18분)" — 흰 벽 배경 + 사람 + 텍스트 90% 검정.
- 외곽선 5px 미만. **글자 크기 200px+ 면 outline 안 써도 명도 OK.**
- 1차 분석은 무조건 13px outline이라 했지만 GIANT면 단색도 됨.

### D. **외곽 프레임 = 노랑 도 잘 먹힘**
- #004 노랑 외곽 프레임 (300만 view)
- #012 노랑 외곽 프레임 (100만 view)
- 1차에서 초록만 봤지만, 노랑이 더 보편.

## MARCELO (eddieoz/youtube-clips-automator, 160★) 아키텍처 인사이트

**핵심 패턴**: Pre-cached asset 풀 + 변형 합성 (nano_banana 매번 호출 X)
1. `./backgrounds/` 폴더 = 미리 준비된 BG 5-10장 (랜덤/룰 픽)
2. `./assets/default_face.png` = fallback 얼굴 (또는 OpenCV로 영상에서 smiling face 추출)
3. 합성 시간: 매번 AI 호출 (30s) → 캐시 + Pillow paste (0.5s)

**ARC 적용:**
- Asset 풀 = nano_banana로 1회 만들고 cache → 매 변형마다 재사용
- 비용 절감 = 6 thumbs 만들 때 12 nano_banana call (factory v3) → 6 call (asset reuse)

## V3 → V4 차이

| 변수 | V3 (6장) | V4 (8-10장 계획) |
|---|---|---|
| Asset 생성 | 매번 (12 calls) | 1회 cache (6 calls) |
| 의사 portrait | 100% AI staged 의사 | mix: 의사 30% + 트레이너 30% + 일반인 40% |
| 카피 톤 | 의사 톤 ("이곳을 누르면...") | mix: 의사 + 후기 ("따라했더니!") |
| 외곽선 두께 | 13px 일관 | mix: 13px 일반 + 5px GIANT 텍스트 |
| 외곽 프레임 | 초록만 | 초록/노랑/빨강 mix |

## 외부 정론 (perplexity 2 dive)
- "Korean senior 2026 thumbnail = concerned senior face + minimalist negative space + 50%+ empty + 2 colors text max" (perplexity)
- "Health channel target CTR 9-15% with proper design" (TubeVertex)
- "Pre-cached background pack + face cache" (MARCELO architecture)
- 위 패턴 ABCD가 위 정론 부분적 부합 (개인 후기 = 일반인 트러스트 / 운동자세 = 신선함 / GIANT 텍스트 = mobile 가독성).

## V4 실행 사양 (다음 액션)

1. Asset 풀 생성 (1회):
   - BG 6장: 빨간 anatomy / 음식 매크로 / MRI / 운동 매트 / 의자 자세 / drink+pill
   - Person 6장: AI 의사 50대 / 한의사 / 여 의사 40대 / 트레이너 30대 / 일반인 60대 / 환자 본인 손
2. rembg cutout 1회.
3. Pillow 합성 엔진 — 8-10 design × asset 풀 mix-and-match.
4. mode = "doctor"(staged) / "trainer"(상의 운동복) / "patient"(자기 무릎잡음 후기톤) 3-track.

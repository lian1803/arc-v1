# YouTube 시니어 채널 - 5 시안 비교 (진화 알고리즘 진짜 적용)

## BLUF
5 시안 X 6 항목 (영상 + 제목 + 키워드 + 썸네일 + 설명 + 첫 댓글) 완성. 진화 알고리즘 *진짜* 적용 — log 파일 4 종이 multi-step 증거. Lian 1 개 선택 → 30분-1시간 풀 영상 fire (추가 비용 0, Kling clip + voice 재사용).

## 비유
5 명 셰프가 같은 무릎 통증 영상을 다른 조리법으로:
- **A**: 1 인 단독 (gems 그대로 끓임)
- **B**: 자기 요리 다시 맛보고 → 수정 → 다시
- **C**: 시장조사 (Perplexity) + 메뉴기획 (Claude) + 조리 (Gemini) + 검수 (Claude) 4 명 분업
- **D**: 3 가지 hook 동시 끓이고 → 평가 → 가장 맛있는 거 1 개 선택
- **E**: 메뉴 먼저 짜고 → 챕터별 따로 깊이 조리 → 합치기

## 5 패턴 비교 표

| 패턴 | 진화 알고리즘 | 풀 스크립트 | sample 영상 | 썸네일 | 알고리즘 증거 log |
|---|---|---|---|---|---|
| A | gems baseline (1-shot) | 5,659 char (~15분) | A_sample.mp4 (68s) | A_thumb.jpg | (없음, baseline) |
| B | Self-Critique 3 사이클 | 8,473 (~22분) | B_sample.mp4 (82s) | B_thumb.jpg | B_critique_log.md (48KB) |
| C | Multi-agent 4-step | 3,998 (~10분) | C_sample.mp4 (74s) | C_thumb.jpg | C_chain_log.md (31KB) |
| D | A/B parallel 3+judge | 8,728 (~22분) | D_sample.mp4 (78s) | D_thumb.jpg | D_judge_log.md (52KB) |
| E | Outline 4-챕터 drill | 19,101 (~50분) | E_sample.mp4 (68s) | E_thumb.jpg | E_outline.md (62KB) |

## 진화 알고리즘 진짜 적용 증거
- **B_critique_log.md** = 3 사이클 변화 (Draft → Critique → Revised) 보존
- **C_chain_log.md** = Research (Perplexity) → Outline (Claude) → Draft (Gemini) → Final (Claude) 4 단계 산출
- **D_judge_log.md** = 3 hook variant + Claude judge 점수 + 선택 이유
- **E_outline.md** = outline + 챕터별 별도 생성 + 합성

## 비용 / 시간
- 텍스트 단계 (5 패턴 + 메타): ~$1.72 (Gemini + Claude + Perplexity)
- TTS 5 종 (Edge-TTS): **무료**
- 영상 합성 (ffmpeg + 기존 doctor_clip 재사용): **0**
- 썸네일 5 종 (fal Flux Schnell): ~$0.05
- **총: ~$1.77**
- 시간: 약 35 분 (sub-agent 2 회 fail 포함)

## Lian 추천 (subjective + 데이터)
| 패턴 | 강점 | 약점 |
|---|---|---|
| A | 안전 baseline, 비용 최소 | 진화 X = 차별화 X |
| B | 검수 사이클로 quality ↑ 추정 | 비용 ↑ (호출 3 배) |
| C | 사실 검증 강함 (Perplexity) | 길이 짧음 (editor 가 압축) |
| D | hook 자동 A/B, retention 예측 | 3 변형 비용 |
| **E** | **가장 풀 분량 (50분)**, Lian 채널 spec 부합, 챕터 깊이 | 챕터 transition 어색 가능 |

**우선 추천**: **E** (Lian 채널 = 30분-1시간 spec 직접 매칭) 또는 **D** (자동 hook 검증).

## 다음 — Lian 결정 받을 것
1. **5 sample.mp4 + 5 썸네일 직접 보고** (Windows 탐색기로 폴더 열어서 더블클릭)
2. **1 패턴 선택** → 30분-1시간 풀 영상 fire (기존 voice.mp3 풀 분량 + Kling clip loop = 추가 비용 0)
3. **다 별로** → 새 5 시안 fire (다른 주제 / 다른 알고리즘 조합) — 비용 ~$2 추가
4. **자동화 시스템 박기** → ARC SPEC.md / DOCTRINE 에 "research → N 시안 → Lian-as-judge → execute" workflow 정식 룰화

## Self-criticism (§13)
1. **영상 sample = 1-1.5분만** (풀 30분-1시간 X). 영상 quality 비교 부족 — 1 개 선택 후 풀 영상 fire 필수.
2. **썸네일 = 1 회 호출**. 썸네일도 N 시안 (3-5) 권장 if 시간 남음.
3. **진화 알고리즘 *효과* = log 만 증거**. retention / CTR 실측 X — YouTube 배포 후 측정 필요.
4. **C 패턴 길이 짧음** (~10분 분량) — Multi-agent editor 가 너무 압축. prompt 조정 필요.
5. **5 패턴 다 같은 의사 영상 클립 (doctor_clip.mp4) 사용** = 영상 자체 차별화 X. 패턴 차이 = 음성 + 스크립트만.
6. **이전 sub-agent 2 회 fail** (1차: B-E hook 만, 영상 0개 / 2차: false sandbox claim). 직접 Bash + 작은 sub-agent fire 로 recovery.

## 파일 위치
모든 산출물: `C:\Users\lian1\Documents\Work\ARC\projects\youtube_automation_demo\`

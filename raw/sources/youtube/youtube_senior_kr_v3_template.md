---
kind: process_playbook
slug: youtube_senior_kr_v3_template
status: active
authored_by: seoyeon-session31
created_at: 2026-04-29
verified_by: lian-2026-04-29 (verbal sign — "이게 금형이야")
sources:
  - https://www.anthropic.com/research/building-effective-agents
  - https://arxiv.org/abs/2303.17651
  - https://arxiv.org/abs/2308.00352
  - https://github.com/rany2/edge-tts
  - https://ai.google.dev/gemini-api/docs/image-generation
---

# YouTube 시니어 한국 채널 — 풀 영상 자동 생성 (v3 금형)

> **Lian 사인 2026-04-29 session 31**: "지금 winner_full.mp4 저거 만든 방법을 템플릿으로 박아. 이제 저게 금형이야."
> 결과 검증: 43분 41초 영상 / 14,424자 enriched 대본 / Hyunsu 목소리 / 비용 ~$0.6.

---

## 1. 한 줄

주제 1개 → **풀 30~50분 시니어 한국어 유튜브 영상 + 썸네일 + 메타** 자동 생성. 사람 손 = Lian 의 1) 주제 결정 + 2) 최종 검수 (영상 1편 시청).

## 2. 언제 쓰나

- 시니어 (60+) 한국어 건강/생활 채널 콘텐츠 1편 빌드.
- 다른 시니어 ICP 도 가능 (단 voice / hook tone 재조정 필요).
- 30분 미만 short-form 은 본 금형 부적합 (분량 prompt 조정).

## 3. 입력

| 항목 | 값 / 위치 | 비고 |
|---|---|---|
| TOPIC | `run_v3_iterate.py:13` `TOPIC` 변수 | 1줄 한국어 주제 |
| GEMS | `C:/Users/lian1/Desktop/새 텍스트 문서 (17).txt` | Lian 의 시니어 채널 스타일 gems (대본 톤 기준) |
| LENGTH | `run_v3_iterate.py:14` `LENGTH` | 기본 17,000~20,000자 (50~55분) |
| VOICE | `gen_v3_final.py:14` `DEFAULT_VOICE` | **Hyunsu (기본)**. Lian 사인 2026-04-29. InJoon/SunHi 대체 가능. |
| BG_CLIP | `projects/youtube_automation_demo/doctor_clip.mp4` | 영상 background loop 1.3MB |
| API keys | `.env` — GEMINI / ANTHROPIC / OPENAI (선택) | OpenAI 없으면 Gemini image 폴백 |

## 4. 실행 절차 (3 step)

```
# Step 1 — 3 라운드 iteration (8~10분 / ~$0.50)
python projects/youtube_automation_demo/run_v3_iterate.py
# 출력: v3_iter/winner_full.txt + winner_meta.json + r1/r2/r3 judge logs

# Step 2 — 분량 부족 시 expand (선택, 1분 / ~$0.10)
# winner_meta.json 의 chars < 12,000 이면 fire
python -c "<expand snippet — README §6.2 참조>"

# Step 3 — 최종 빌드: 쉼표 풍부화 → TTS → 영상 합성 → 썸네일 → 메타 (8~10분 / ~$0.05)
python projects/youtube_automation_demo/gen_v3_final.py
# 출력: v3_final/winner_full.mp4 + winner_full.mp3 + sample_{InJoon,Hyunsu,SunHi}.mp3
#       + thumb.jpg + metadata.json + winner_enriched.txt
```

## 5. 출력 7 파일

| 파일 | 크기 | 용도 |
|---|---|---|
| winner_full.mp4 | ~300 MB / 43~50분 | 업로드용 풀 영상 |
| winner_full.mp3 | ~16 MB | 오디오 only (팟캐스트 / 백업) |
| sample_{InJoon,Hyunsu,SunHi}.mp3 | ~340~400 KB | A/B/C voice 비교 (첫 400자) |
| thumb.jpg | ~1.5 MB / 1792x1024 | 썸네일 |
| metadata.json | ~1.5 KB | title / 키워드 10 / 챕터 6 / pinned comment |
| winner_enriched.txt | ~33 KB | 최종 대본 (검수 / 자막 추출 용) |

## 6. 알고리즘 (왜 이게 작동하나)

### 6.1 Iteration: Round 1 (D 패턴) → Round 2 (B 패턴) → Round 3 (judge)
- **R1** = 3 hook variant (결과미리 / 내부고발 / 환자스토리) → Claude judge (retention/TTS적합성/감정 1-10) → best.
- **R2** = R1 winner 를 self-critique → revise (Self-Refine 패턴, Madaan 2023).
- **R3** = R1 winner vs R2 revised 비교 judge → final.
- **세션 31 발견**: R3 가 R2 (over-comma 7.68/100자) 보다 R1 (자연스러운 2.5/100자) 을 선호. **쉼표 over-pack = 부자연 = retention 손해.**

### 6.2 Expand (선택)
- Gemini Pro 가 한 번에 ~10,000자 cap → 17,000자 spec 미달 시 expand 호출.
- Prompt 룰: "기존 흐름 유지 + 환자 사례 +2 / 운동 +2 / Q&A 섹션 + 깊은 과학 설명".

### 6.3 Comma Enrichment (Claude 7K 청크별)
- TTS pacing 호흡 단위 분리. 한 문장당 평균 3-4 쉼표.
- 한글 숫자 / 단어순 변경 금지.

### 6.4 TTS — Edge-TTS Korean Neural
- **Default = Hyunsu** (Lian sign 2026-04-29).
- 비용 = 0 (무료, Microsoft Cognitive 무인증).
- 풀 14,000자 = ~44분 mp3.

### 6.5 Video Synth — ffmpeg loop
- doctor_clip.mp4 (1.3 MB / 9초) 를 audio 길이만큼 stream_loop.
- libx264 / yuv420p / 30fps. ~301 MB / 44분.
- **약점 (Lian 인지)**: 같은 클립 loop = 시각 단조. 1차 retention drop risk. B-roll 추가 = 다음 iteration.

### 6.6 Thumbnail — Gemini 2.5 Flash Image
- 1차 시도 = DALL-E 3. 2026-04-29 OpenAI billing hard limit → Gemini image 자동 폴백.
- aspectRatio 16:9, photorealistic.

### 6.7 Metadata — Claude
- Title (60자) / 키워드 10 / 설명 (300-500자, 챕터 6 timestamps + CTA + 해시태그) / pinned comment.

## 7. 비용 / 시간

- **API**: Gemini Pro (iter+expand) ~$0.40 + Claude (judge+critique+enrich+meta) ~$0.15 + Gemini image ~$0.01 ≈ **$0.6** / 영상.
- **시간**: ~22~25분 (iter 8 + expand 1 + final 8 + thumb 30s + 버퍼).
- **수동 시간**: Lian 검수 = 영상 1번 시청 (44분) + voice 샘플 3개 비교 (~30초).

## 8. Falsifier (§A1)

- 다른 주제 (예: 당뇨, 고혈압, 치매 예방) 로 재실행 시 자율 quality 점수 ≥35/40 안 나오면 = **over-fit, 템플릿 실패**. 첫 5 주제 전수 검증 권장.
- 쉼표 enrichment 가 5/100자 초과 시 = R3 룰 위반, 재생성.
- 영상 길이 < 25분 = 시니어 채널 spec 미달, expand 재실행.

## 9. 외부 정론 비교 (§13 준수)

- **Anthropic "Building Effective Agents"** (2024-12) — Multi-agent reflection + judge 패턴 권장. 본 금형의 R1/R3 judge 와 정렬.
- **Self-Refine (Madaan 2023, arxiv 2303.17651)** — iterative critique → revise. R2 와 정렬. 동의.
- **MetaGPT (Hong 2308.00352 v6)** — role-specific dispatch. 본 금형은 Gemini=generator / Claude=critic+judge 분업. 동의.
- **edge-tts (rany2 OSS)** — 무료 Korean Neural voice 검증. Hyunsu = 가장 자연스러운 시니어 남성 톤 (Lian 청취 검증 2026-04-29).
- **Gemini Image API** (Google 2025) — DALL-E 폴백 안정. 동의.

5/5 동의 → 본 금형 외부 정론 정렬됨.

## 10. 다음 iteration 시 검토 항목

- B-roll: doctor_clip 1개 → 다양한 stock clip 3-5개 cycling (retention 약점 보강).
- Voice 다양화: 한 영상 내 의사 (Hyunsu) + 환자 voice (SunHi) 분기 (ElevenLabs 같은 multi-voice TTS 검토).
- Auto-upload: YouTube Data API 연동 (현재 = 수동).
- A/B 썸네일: 3 prompt 동시 생성 → CTR 실측 (1주 데이터 후 winner 채택).

## 11. Carry / 한계

- DALL-E 3 quota = OpenAI account 의존. Gemini 폴백 박혀있어 자동 복구 가능.
- Gems 파일 경로 hardcoded (`Desktop/새 텍스트 문서 (17).txt`) — 다른 주제로 옮길 때 GEMS 분리 필요.
- 의료법: 본 금형은 "정보 제공" tone. "치료/완치" 단어는 R1 hook prompt 에서 제외 권장.

## Ref

- Source code: `projects/youtube_automation_demo/run_v3_iterate.py` (125 LOC) + `gen_v3_final.py` (123 LOC).
- 첫 산출물: `projects/youtube_automation_demo/v3_final/winner_full.mp4` (2026-04-29).
- 결정문: 본 파일 (Lian sign 2026-04-29).
- 외부 research (예정): `shared/knowledge/youtube_senior_kr_metadata_research.md` (키워드/제목/썸네일 시장 conventions).

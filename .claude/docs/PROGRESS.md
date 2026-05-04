# PROGRESS — ARC 매일 누적

> 매 세션 끝에 한 줄 추가. Lian 결심 "매일 조금씩" 정합.
> 형식: `## YYYY-MM-DD` + `한 일:` + `다음:`. 길게 쓰지 X (NEXT.md가 디테일 담당).

---

## 2026-05-03 (시스템 디벨롭의 날)

**한 일:**
- 외부 perplexity 3차 검색 (총 15쿼리, 100+ 출처): buildgap / solopreneur standard / develop
- ARC 방향 외부 정론 정합 확인: ARC = day 1-5 자연 단계, Luna = enterprise 패턴 (carry over X)
- Luna 자산 carry: 시뮬 도구 6개 (tools/sim/) + 실패 학습 4개 (raw/molds/failed/) + 외부 사례 3개 (raw/molds/external/) + cost 도구 2개 (tools/cost/) + citation_verify
- ARC CLAUDE.md / MODES.md 수정: sub-agent 호출 룰 삭제, "Lian + Cursor/Claude 1대1" + "30일 죽일 기준" + "빌드 끝 시뮬 PASS" 추가
- raw/molds/my/ 첫 사례 박음: test_run_001_haircare_loyalty (정수민, 화곡동) 표준 YAML 헤더
- NEXT.md 생성 (다음 세션 cold start 방지)
- raw/sources/INDEX.md 생성 (4개 통합본 라우팅)

**추가 (세션 종료 직전 Lian 요청):**
- `tools/search/` 신설: dive.py (메인) + pplx.py + browse.py + yt.py (luna carry, import 패치) + README. 한 쿼리 → perplexity + 모든 citation 자동 fetch (YouTube transcript 한국어 우선) → 통합본 1장. 1회 ≈ $0.01.
- `tools/search/` 추가 4개 모듈 (Lian 추가 요청): reddit_dive (Reddit 무인증 JSON), hn_dive (Algolia + Firebase), github_dive (API, 옵션 GITHUB_TOKEN), twitter_dive (nitter best-effort, 작동 보장 X). 모두 독립 실행 가능, dive.py와 통합은 다음 버전.

**추가 (5/3 밤 — selfie 작업으로 확장):**
- `tools/image/nano_banana.py` — Gemini 2.5 Flash Image API (generate/edit/fuse). 2장 실 셀카 편집 PASS (귀걸이 + UI 아이콘 제거).
- `tools/image/sharpen.py` — PIL 6가지 sharpen (unsharp/detail/edge/sharpness/contrast/compose). 사진 편집기 "선명도" 효과.
- `tools/image/upscale.py` — fal.ai 5종 (clarity/face/codeformer/esrgan/aura). 단 fal 잔고 소진 — 충전 필요 시 재가동.
- `tools/search/` 5개 추가 모듈 (reddit/hn/github/twitter/gemini_dive) + dive.py 통합 옵션 + _compact_query 버그 fix.
- ★ **projects/selfie_factory/** ARC 첫 진짜 프로젝트 박음 (scratch own itch). PLAN/README/사례 등록 (raw/molds/my/ 1→2).

**다음 (2026-05-04 첫 30분):**
- ★ **selfie_factory 첫 사용** — refs/me/ 본인 셀카 5-10장 배치 + refs/style/ Pinterest 1장 + fuse 1세트 시도. 5분 내 만족 = 첫 빌드 PASS.
- (선택) test_run_002 PLAN.md 1장 작성 (인보이스 자동독촉)
- 시스템 작업 비중 ≤30% (Pilot Graveyard 회피)
- 30일 후 2026-06-03 = selfie_factory 죽일/살릴 결정 체크

**경고:**
- 외부 정론 Q5: "사업 launch 1건 전엔 시스템 디벨롭 금지" — 오늘 위반함 (의식적 결정).
- 사업 launch 0건 = 외부 정론상 "Pilot Graveyard 입구". 내일 빌드 시작이 정답.

---

## 2026-05-04 (YouTube 썸네일 공장 체인 빌드)

**한 일:**
- luna `projects/youtube_automation_demo/` 통째로 ARC carry (76 파일 / 780MB) + tools/youtube_scout.py + raw/sources/youtube/ 8개 knowledge
- 환경 fix: Python 3.14 + edge_tts/dotenv/rembg/onnxruntime 설치, ffmpeg winget install, 경로 5개 (Desktop/Documents 하드코딩 → ROOT relative) 패치, gems_base.txt placeholder
- ★ 사고: `run_v3_iterate.py` 백그라운드 테스트가 v3_iter/winner_full.txt (8430자) 덮어씀 → enriched + mp4 무사, R3 winner 텍스트만 손실
- 썸네일 폭격: fal 잔고 X / OpenAI hard limit / Gemini만 살음. 33장 생성 (BULK_GEMINI 16 + TOPYT_V2 12 + 5)
- 외부 학습: yt.py wide corpus 60장 (5만~497만 view) + perplexity dive 2회 + GitHub `eddieoz/youtube-clips-automator` (160★ MARCELO) 패턴
- factory_v3 (1세트마다 nano_banana 2회) → factory_v4 (asset cache + 3-track 톤 mix) → ★ **factory_v5_lian** (E:\유튜브\1계정 50장 분석으로 brand 정확 spec 추출)
- raw/sources/youtube/에 분석 3개 박음: topyt_무릎통증_pattern / topyt_무릎_corpus_v2 / **lian_1account_brand_spec** (가장 중요)
- V5 = 검정 배경 + 노랑 텍스트 + 의사 portrait + 우상단 노년황금기 뱃지 + 99% 인용 — 리안 본인 채널 톤 정확 매치 8장

**다음 (2026-05-05):**
- 썸네일 = 더 테스트 / 변형. nano_banana 캐시 활용 = 변형마다 $0
- selfie_factory or test_run_002 PLAN — 옵션 A 사업 launch 트랙 복귀 (시스템 비중 ≤30% 룰 위반 누적 중)

**경고 (누적):**
- 5/3 + 5/4 모두 시스템 작업 위주. 사업 launch 0건 = Pilot Graveyard 더 깊어짐. 다음 세션 1순위 = 사업 launch 트랙.

---

## 2026-05-04 (오프라인 직전 마감 — ARC 인프라 마무리)

**한 일:**
- ARC 루트 청소: `.tmp_*` 30개 → `archive/2026-05_root_cleanup/` (5 카테고리 보존). luna §14 정합 후행.
- 자동 라우팅 hook: `.claude/hooks/route_root_writes.py` PreToolUse(Write|Edit) 화이트리스트 외 루트 신규 파일 차단 (exit 2). 스모크 9/9 PASS.
- `.claude/rules/file-routing.md` 박음 (토글 4섹션). `.gitignore` 신설 (.env / .tmp_* / 영상 / 캐시).
- 루트 .md 4개 → `.claude/docs/` (MODES/NEXT/PREMISES/PROGRESS). CLAUDE.md @import 4줄 + 본문 압축 = 24/30줄. 루트 항목 14 → 10.
- git 신규: `.git` 폐기 + Git for Windows 2.54.0 설치 + 새 init + first commit 987 files / 244,470 lines + push → https://github.com/lian1803/arc-v1 (public).
- Cursor dive 2회 ($0.02): Cursor 3 (4월 출시 Background Agents/Composer 2/Agent Window) + 5월 점유율 31% AI IDE 1위. ARC MODES.md "Cursor/Claude 1대1" 외부 정론 정합 확인.
- ★ marketing_agency 호환성 연결: luna 통째 carry (7 sub-project + _shared) → `raw/molds/my/marketing_agency.md` mold 등록 / NEXT.md 진행 사업 #4 추가 / CLAUDE.md ARC integration 섹션 luna DOCTRINE 참조 → ARC 시스템 룰 매핑.
- ★ Cursor 양방향 핸드오프 시스템: `.claude/rules/handoff.md` (Claude Code 측) + `.cursor/rules/{arc,modes,handoff,file-routing}.mdc` 4개 (Cursor 측 미러) + CLAUDE.md 라우터 1줄. AI가 작업 분산 자동 판단 → Lian은 복붙만. CLAUDE.md 25/30.
- ★ AGENTS.md cross-tool baseline 추가 (dive 4번째 검증 결과 박음): destructive 차단 (PocketOS Cursor agent 9초 DB 삭제 사례) + 권한 스코프 (Local/Staging/Production) + post-handoff git diff 검증. CLAUDE.md @AGENTS.md import (26/30). hook WHITELIST + file-routing 화이트리스트 갱신. handoff.md/mdc §5 git status/diff 명시 강화.

**다음 (2026-05-05):**
- 옵션 A 1순위 — sales_offline (마케팅 에이전시 메인) 또는 test_run_002 PLAN 1장. 시스템 작업 5/3+5/4+오늘 누적 위반 마감.
- selfie_factory 첫 사용도 옵션 A 후보.

**경고 (계속):**
- launch 0건 유지. 다음 세션 = PLAN.md 1장이 첫 동작.

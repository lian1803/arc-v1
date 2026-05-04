# 파일 라우팅 룰

> 새 파일 만들기 전 self-check. 루트 cap = 5 .md + .env + .cost_log.jsonl + .gitignore.
> 강제: `.claude/hooks/route_root_writes.py` (PreToolUse Write|Edit 차단).

<details>
<summary><b>루트 화이트리스트</b> (이거 외엔 루트에 못 만듬)</summary>

**파일**:
- `CLAUDE.md` — 3원칙 + 라우터 + @import (30줄 cap)
- `AGENTS.md` — Cursor + Claude Code 둘 다 읽는 cross-tool universal (destructive 차단 / 권한 스코프 / post-handoff 검증)
- `.env`, `.env.example`, `.gitignore`, `.cost_log.jsonl`

**폴더**:
- `.claude/`, `.git/`, `archive/`, `projects/`, `raw/`, `tools/`

**`.claude/docs/` 안** (CLAUDE.md @import 대상):
- `MODES.md` — Phase 1 기획 / Phase 2 빌드
- `NEXT.md` — 다음 세션 cold start 가이드
- `PREMISES.md` — 빌드 전제
- `PROGRESS.md` — 매일 누적 로그

추가 시 Lian 명시 동의 + 본 룰 갱신.

</details>

<details>
<summary><b>패턴별 라우팅</b></summary>

| 패턴 / 종류 | 위치 |
|---|---|
| `.tmp_*`, `temp_*`, `scratch_*` | `archive/scratch/YYYY-MM/` |
| 외부 자료 통합본 (perplexity / dive / 유튜브 분석) | `raw/sources/{slug}_YYYY-MM-DD.md` |
| 외부 자료 raw (json / log / dump) | `raw/sources/_raw/YYYY-MM/` |
| 내 사례 | `raw/molds/my/{slug}.md` |
| 외부 사례 | `raw/molds/external/{slug}.md` |
| 실패 사례 | `raw/molds/failed/{slug}.md` |
| LIVE 사업 | `projects/{name}/` |
| 검색 도구 | `tools/search/` |
| 이미지 도구 | `tools/image/` |
| 비용 도구 | `tools/cost/` |
| 시뮬 | `tools/sim/` |
| 보존 (참조 X) | `archive/{topic}/` |

</details>

<details>
<summary><b>새 폴더 만들기 전 체크</b></summary>

1. 위 표 안에 들어가? → 그 자리.
2. 안 들어가? → Lian 동의 + 본 룰 표 갱신.
3. 1회성 실험? → `archive/scratch/YYYY-MM/` 안에서 끝내라.
4. 깊이 ≤ 3 (`tools/search/_legacy/`까지). 더 깊이 = 재구조화 신호.

</details>

<details>
<summary><b>차단 메시지가 떴을 때</b></summary>

hook이 차단하면 stderr에 안내 뜸. 두 경우:

- **`.tmp_*` 신규** → `archive/scratch/2026-05/` 로 경로 바꿔서 재시도.
- **그 외 화이트리스트 외 루트 파일** → 패턴별 라우팅 표 보고 적절한 폴더로 재시도. 진짜 루트가 맞으면 본 룰 + CLAUDE.md 화이트리스트 갱신 + Lian 동의.

</details>

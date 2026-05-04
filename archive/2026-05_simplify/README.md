# 2026-05-04 Cursor 룰 단순화

복잡도 줄이려고 `.cursor/rules/` 3개 archive 이동.

## 이동 대상

| 파일 | 이전 역할 | 복귀 조건 |
|---|---|---|
| `arc.mdc` | CLAUDE.md 미러 (ARC 3원칙) | Cursor가 큰 그림 작업 받기 시작하면 |
| `modes.mdc` | Phase 1/2 미러 | Cursor가 Phase 1 (PLAN 작성) 받기 시작하면 |
| `file-routing.mdc` | 파일 라우팅 미러 | Cursor가 새 파일 위치 자체 결정 자주 하면 |

## 활성 (남은 것)

- `.cursor/rules/handoff.mdc` — Cursor → Claude Code 핸드오프 트리거
- `AGENTS.md` (루트) — Cursor + Claude Code 둘 다 읽음 (destructive/권한/라우팅)

## 운영 3문장

> **큰 그림은 Claude, 파일 수정은 Cursor, 막히면 다시 Claude.**

이 3문장 + handoff 2개 + AGENTS.md = 80% 커버. 처음엔 작게.

## 근거

- 사용자 메모리 `스몰 + 단단함` (2026-05-03)
- ARC v3 "얇아라" 1번 원칙
- 사용자 호소: "도대체 뭔 소리고 어떻게 써야 하는지 모르겠다"
- Perplexity 외부 시각: "처음엔 핵심 규칙 2개만으로 충분"

## 복귀 방법

archive에서 `.cursor/rules/` 로 다시 복사. §6 Accumulate-Never-Delete 정합.

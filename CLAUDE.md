# ARC — 금형공장

ARC = Lian이 사업 N개 굴릴 때 쓰는 인프라.

@AGENTS.md
@.claude/docs/MODES.md
@.claude/docs/PREMISES.md
@.claude/docs/NEXT.md
@.claude/docs/PROGRESS.md

## 3원칙

1. **얇아라** — 매뉴얼 < 사례. 30줄 cap. 위반 시 자동 분리.
2. **알아먹어** — Lian 한 줄 → 의도 1줄 재진술 + raw/molds/ 사례 1-2 매칭. generic 금지.
3. **쉽게 답해** — 비유 첫 줄. BLUF (결론 → 이유 1줄 → 위험 1줄).

## 라우터

- 사례 → raw/molds/{my|external|failed}/ / 외부 자료 → raw/sources/
- LIVE 사업 → projects/{이름}/ / 도구 → tools/{search|image|cost|sim}/
- 보존 → archive/ / 파일 위치 룰 → .claude/rules/file-routing.md (hook 작동)
- Cursor 핸드오프 → .claude/rules/handoff.md (양방향 자동 분산)

## Gate

- Reach: ICP가 5분 안에 자기 손으로 쓸 수 있나? NO → 재설계.
- 빌드 끝: tools/sim/ 페르소나 시뮬 PASS = 끝. FAIL = 재빌드. 시뮬 X = 끝 X.

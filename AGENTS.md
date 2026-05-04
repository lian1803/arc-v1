# AGENTS.md — Cross-Tool Baseline

> Cursor + Claude Code 둘 다 읽는 universal. ARC 시스템 룰은 CLAUDE.md / .cursor/rules/arc.mdc 참조.
> 핸드오프는 .claude/rules/handoff.md / .cursor/rules/handoff.mdc.

## Destructive Operation = Lian 명시 동의 필수

위반 시 즉시 stop + Lian 명시 확인 후 진행. **2026-04 PocketOS 사례**: Cursor agent가 9초만에 production DB + 백업 삭제 ("guessed wrong on scopes"). 30시간 outage.

- **DB**: `DROP TABLE`, `DELETE FROM ... WHERE` (full), `TRUNCATE`, prod schema migration
- **파일**: `rm -rf`, `Remove-Item -Recurse -Force` (홈·시스템·archive 외)
- **Git**: `push --force`, `reset --hard` (shared branch), `branch -D`, `clean -fdx`, history rewrite
- **외부 호출**: 결제, 메일/카카오/문자 발송, webhook trigger, API key 회전
- **권한**: chmod/chown, AWS IAM, Cloudflare API 토큰 변경

## 권한 스코프

- **Local** (D:\work\ARC\): 자유
- **Staging** (배포된 dev/test): commit·push 자동 / deploy = Lian 동의
- **Production** (live 사업·결제·DB·외부 호출): 모든 수정 Lian 명시 동의

## Post-Handoff 검증 (도구 전환 직후 첫 동작)

1. `git status --short` + `git diff --stat`로 변경 파일 확인
2. 의도 외 파일 변경 있으면 stop + 보고
3. raw/molds/my/{slug}.md `actions.done` 한 줄 추가
4. 다음 동작 결정 또는 다음 핸드오프

## 사례·외부 자료 라우팅

`raw/molds/{my|external|failed}/` / `raw/sources/{slug}_YYYY-MM-DD.md` / `tools/{search|image|cost|sim}/` / `archive/`

# Handoff Rule — Claude Code ↔ Cursor 자동 분산

> Lian이 도구 분산 결정 안 해도 됨. AI가 작업 중 자동 판단 → 복붙 프롬프트 박스 출력.
> 양방향: 본 룰 (.claude/rules/handoff.md) + Cursor 측 (.cursor/rules/handoff.mdc) 미러.

---

## 1. 언제 Cursor로 넘기나 (트리거)

다음 중 하나라도 해당 = 즉시 핸드오프 출력:

- **Tab 자동완성·인라인 빠른 편집** 다수 발생 예상 (한 줄~한 파일 안 작은 수정 5개+)
- **여러 파일 동시 수정** (multi-file refactor, Composer 2 가 더 빠름)
- **UI / 디자인 시각적 반복** (Cursor Design Mode)
- **Background Agent 병렬 작업** (PR 자동 생성, 테스트 작성 동시 다수)
- Lian이 명시적으로 "Cursor로 넘겨" / "이건 커서가 빠르겠는데"

## 2. 언제 Cursor에서 못 받음 (Claude Code 유지)

- **전체 코드베이스 분석** (100만 토큰 컨텍스트 필요)
- **큰 리팩토링** (다중 단계, 아키텍처 변경)
- **터미널 명령 자동화** (git, npm, 빌드, 배포)
- **외부 검색 + 긴 사고 + 의사결정** (지금 이 세션 같은)
- **ARC 시스템 룰 활용** (`.claude/` 자동 로드, hook 검증, raw/molds 사례 매칭)
- **PLAN.md 1장 작성** (MODES.md Phase 1, 대화·검증 길게)

## 3. 출력 형식 (정확히 이 형태로)

핸드오프 발동 시 답변 마지막에 박스로:

```
🟢 리안, 여기서부터는 Cursor가 할 일이야.

Cursor 에이전트 창(Cmd/Ctrl+L)에 이 프롬프트 그대로 복붙:

----- 복붙 시작 -----
[작업 컨텍스트 1줄]
[현재까지 한 일 bullet 3개 이내]
[Cursor가 할 일 bullet 3개 이내]
[컨텍스트 파일 절대경로]
끝나면 답변 마지막에 "🟣 클로드코드로 가" 박스 + 결과 1줄 요약 + Lian이 클로드코드 터미널에 복붙할 프롬프트 박스 출력.
----- 복붙 끝 -----

작업 끝나면 클로드코드 터미널에 와서 "커서 끝났어" 한 마디 + 결과 1줄.
```

## 4. 컨텍스트 인계 룰

- **파일 경로**: 항상 절대경로 (D:\work\ARC\...). Cursor가 다른 작업 디렉토리일 수 있음.
- **현재 상태**: git commit hash 또는 "uncommitted N files" 명시.
- **PLAN reference**: 진행 중 사업이면 `projects/{name}/PLAN.md` 또는 `raw/molds/my/{slug}.md` 가리킴.
- **금지**: 모호한 "그것/저것" 사용 X. 항상 명시.

## 5. Cursor 끝나고 돌아올 때

Lian이 "커서 끝났어" 또는 "🟣 클로드코드로 가" 박스 내용 복붙하면:

1. 변경된 파일 git status / diff 로 확인
2. raw/molds/my/{slug}.md `actions.done` 한 줄 추가
3. 다음 동작 결정 또는 다음 핸드오프 또는 commit

## 6. 자기 점검

매 응답 끝에 self-check: "이 답변에 §1 트리거 발동했나? 발동했는데 핸드오프 안 박았으면 룰 위반. 다시 박기."

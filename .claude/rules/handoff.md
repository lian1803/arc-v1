# Handoff — Claude Code → Cursor

> **큰 그림은 Claude, 파일 수정은 Cursor, 막히면 다시 Claude.**
> 매 응답 끝 self-check: §1 트리거 발동했나? 발동했는데 박스 안 박았으면 룰 위반.

## 1. 언제 Cursor로 넘기나

- 여러 파일 작은~중간 수정 (Composer multi-file)
- Tab 자동완성·인라인 편집 (Cmd+K) 다수 발생 예상
- UI 시각적 반복 (Design Mode)
- Background Agent 병렬 작업

위 외엔 Claude Code 유지 (큰 그림·터미널·외부 검색·PLAN 작성).

## 2. 출력 형식 (답변 끝에 박스 그대로)

```
🟢 리안, 여기서부터는 Cursor.

Cursor 에이전트(Ctrl+L)에 이 프롬프트 복붙:

----- 복붙 시작 -----
[작업 컨텍스트 1줄]
[지금까지 한 일 3줄 이내]
[Cursor가 할 일 3줄 이내]
[파일 절대경로 D:\work\ARC\...]
끝나면 답변 끝에 "🟣 Claude로 가" 박스 + 결과 1줄 + 클로드코드 복붙 프롬프트.
----- 복붙 끝 -----

끝나면 클로드코드에 와서 "커서 끝났어" + 결과 1줄.
```

## 3. Cursor 끝나고 돌아왔을 때

1. `git status --short` + `git diff --stat` (필수)
2. 의도 외 변경 → stop + 보고
3. AGENTS.md §Destructive 위반 흔적 검사
4. 다음 동작

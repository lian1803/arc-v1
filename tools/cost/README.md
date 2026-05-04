# tools/cost — API 비용 관리 (1인 비용 민감 정합)

luna에서 carry. 경로만 ARC 구조에 맞게 패치 (shared/ 폴더 X).

## 파일

- `cost_log.py` — perplexity / Anthropic / OpenAI / Gemini 호출 비용 JSONL 로깅. `.cost_log.jsonl` (root 숨김).
- `cost_gate.py` — 누적 비용이 cap 초과 시 차단 (default: session $5 / day $20 / month $200).

## 사용 (수동, 의무 X)

```python
from tools.cost.cost_log import log
log("perplexity:sonar-pro", metadata={"requests": 5})
```

```bash
python tools/cost/cost_gate.py --window-hours 24
# exit 0 = OK / exit 2 = cap 초과
```

## ARC 정신 정합

- **의무 X (lazy)** — 사용자 결정. "매일 조금씩" 진척에 비용 부담 신호 잡고 싶을 때만 켜기.
- **자동화 hook X** — sub-agent 망 회피와 결 같음. 1인은 직접 결정.
- **shared/config.json 의존 X** — ARC root에 `.cost_config.json` 두면 override, 없으면 DEFAULT_CAPS.

## carry over 시 변경 (luna → ARC)

- `LOG_PATH`: `shared/knowledge/cost_log.jsonl` → `.cost_log.jsonl` (root 숨김)
- `CONFIG`: `shared/config.json` → `.cost_config.json` (optional)
- 코멘트 내 luna spawn.py / message_pool 경로 참조 = 작동 무관, lazy 정리.

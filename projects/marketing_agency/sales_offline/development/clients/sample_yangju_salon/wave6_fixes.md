# Wave 6.5 — CRITICAL 자동 수정 기록

## CRITICAL: 배치 크롤링 IP 차단 대비 부재

### Gemini 지적
> 배치 크롤링 중 네이버 Captcha 등장 시 Playwright가 멈추고 후속 업체 진단이 올스톱됨.

### 수정 내용 (`services/batch_processor.py`)

1. **랜덤 딜레이**: 고정 3초 → 랜덤 5~10초 (`random.uniform(delay_min, delay_max)`)
2. **연속 실패 감지**: 3연속 실패 시 60초 쿨다운 자동 대기
3. **딜레이 자동 증가**: 쿨다운 후 딜레이 범위 2배로 증가 (10~20초)
4. **상태 표시**: 쿨다운 중 상태를 `paused_cooldown`으로 표시 (FE에서 인지 가능)

### 기존에 이미 있던 대비책
- User-Agent 로테이션 (5종) — `naver_place_crawler.py`
- 개별 업체 실패 시 skip 후 계속 진행 — `batch_processor.py`
- 경쟁사 크롤링 실패 시 업종별 평균값 폴백 — `competitor.py`

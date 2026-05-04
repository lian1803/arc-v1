# 2차 저장 — 에이전트 3개 검수 + 서연 직접 검증 (2026-04-28)

## 검증 결론: 에이전트 주장 3/3 코드로 확인됨

### 검증 1: owner_reply_rate 30% 하드코딩 [확인]
- naver_place_crawler.py L1135: `estimatedReplyRate = 0.3;` (상수값 박힘)
- 사장님 키워드("사장님/대표/관리자") 텍스트 1개만 있어도 30%로 고정
- 실제 답글률 아님 — 휴리스틱 추정값

### 검증 2: ai_first_message CLI 미구현 [확인]
- run_one_to_md.py에서 personalize_first_message / ai_first_message 호출 없음 (grep 빈 결과)
- 웹 API(routers/crawl.py L369)에만 있음

### 검증 3: naver_place_rank=0 9/12, receipt_review=0 전부 [확인]
- rank=0: 강남스타벅스, 홍대미용실, 카페버드앓이, 엄지네한식뷔페, ERC영어, 그림아트, 마이샵, 아이결, 레이크스토어
- receipt_review=0: 12/12 전부 (필드 미수집 확정)

## 에이전트 추가 발견 (검증됨)

### A (기능 갭): CLI vs API 갭 14개 필드
- HIGH: ai_first_message
- MED: photo_quality_score, related_keywords, review_sentiment_score
- LOW: place_url, intro_text_length 등 7개
- PDF 직접 영향: 0개 (현재 template_10 기준)

### B (크롤러): 구조적 취약점
- competitor_avg 600/500/300 = 경쟁사 크롤링 실패 시 config 폴백값 (config/industry_weights.py)
- photo_urls 최대 15개 제한 + /photo 페이지 URI 하드코딩 (restaurant, place만)
- bookmark_count: 텍스트 "저장 N" 패턴 미매칭 시 항상 0

### C (데이터 품질): PDF 신뢰도 65/100
- P0 긴급: rank=0 75% → PDF에 "순위권 밖" 표시 (자영업자 신뢰 치명적)
- P1 높음: 0값 표현 방식 ("사진 0장", "리뷰 0개") 개선 필요
- receipt_review_count 필드 비활용 (삭제 또는 활성화)

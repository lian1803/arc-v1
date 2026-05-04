# 소상공인 네이버 플레이스 영업툴 — FE 개선사항 (2026-04-04)

## 요약
비대면 클로징 UX를 개선하여 영업 단계별 메시지 관리와 시각적 피드백을 강화했습니다.

---

## 개선사항 상세

### 1. result.html — 비대면 영업 플로우 안내 + 5차 탭

#### 추가된 요소:
1. **비대면 영업 플로우 요약 카드** (접을 수 있는 details 요소)
   ```
   1단계: 콜드DM (1차 메시지 복사) → 카톡/문자 발송
   2단계: 응답 오면 PPT 다운로드 후 전송 + 2차 메시지
   3단계: 3차 메시지 (패키지 제안 + 손익분기 계산)
   4단계: 이의 있으면 4차 (보류/무응답/비싼/직접 대응)
   5단계: 계약 → 5차 (결제 링크 + 계약서)
   ```

2. **메시지 탭 개선**
   - 각 탭에 "언제 보내는지" 설명 추가
   - 탭 디자인: 그리드 레이아웃으로 변경 (각 탭이 독립적인 카드)
   - 활성 탭: 초록색 배경 + 그림자 효과

3. **5차 탭 추가**
   ```html
   <div id="tab-panel-5" class="tab-panel">
       <!-- 계약 의향 확인 후 결제/계약서 발송용 -->
       {% if messages.fifth %}
           <!-- 5차 메시지 표시 -->
       {% else %}
           <!-- "아직 생성되지 않음" 메시지 -->
       {% endif %}
   </div>
   ```

#### Backend 연동 필요:
- `app.py` 또는 결과 페이지 렌더링 함수에서 `messages.fifth` 생성 필수
- 5차 메시지는 계약 의향 단계에서만 생성되도록 조건 처리

---

### 2. history.html — 영업 단계 추적

#### 추가된 요소:
1. **각 업체 행에 영업 진행 단계 드롭다운**
   ```html
   <select onchange="updateSalesStage({{ history.id }}, this.value)">
       <option value="미접촉">📌 미접촉</option>
       <option value="1차발송">📤 1차발송</option>
       <option value="2차발송">📤 2차발송</option>
       <option value="3차발송">📤 3차발송</option>
       <option value="4차발송">📤 4차발송</option>
       <option value="계약완료">✅ 계약완료</option>
       <option value="거절">❌ 거절</option>
   </select>
   ```

#### 기능:
- 드롭다운 변경 시 `localStorage` 에 임시 저장
- 토스트 알림으로 변경 확인
- 새로고침해도 선택값 유지

#### Backend 연동 필요:
- `history` 테이블에 `sales_stage` 컬럼 추가 권장
  ```sql
  ALTER TABLE history ADD COLUMN sales_stage VARCHAR(20) DEFAULT '미접촉';
  ```
- POST 엔드포인트: `/api/businesses/{history_id}/sales-stage` 추가
- 현재는 localStorage로 임시 저장되므로 필요시 DB 동기화

---

### 3. message_tabs.js — 복사 버튼 피드백 개선

#### 개선사항:
1. **복사 성공 시 버튼 상태 변경**
   - 텍스트: "카카오용 복사" → "✓ 복사됨!"
   - 색상: 노란색(#FEE500) → 초록색(#10B981)
   - 지속시간: 2초

2. **토스트 알림 추가**
   ```
   화면 우측 하단에 초록색 체크마크 + "메시지가 클립보드에 복사되었습니다!"
   2초 후 자동 사라짐
   ```

#### 코드 변경:
- `copyMessage()` 함수 개선
- `showCopyToast()` 함수 신규 추가

---

### 4. history_filter.js — 영업 단계 저장 함수

#### 추가된 함수:
1. `updateSalesStage(historyId, stage)`
   - localStorage 에 `sales_stage_{historyId}` 키로 저장
   - 토스트 알림 표시

2. `showStageUpdateToast(message)`
   - 파란색 토스트 알림 (복사와 구분)
   - 2초 자동 사라짐

#### 사용 예:
```javascript
updateSalesStage(123, '1차발송');
// localStorage 에 저장: { "sales_stage_123": "1차발송" }
```

---

### 5. style.css — 스타일 개선

#### 변경사항:

1. **메시지 탭**
   ```css
   .message-tabs {
       display: grid;
       grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
       gap: 0.75rem;
   }
   ```
   - 반응형 그리드 레이아웃
   - 각 탭이 최소 120px, 자동으로 확장

2. **활성 탭 스타일**
   ```css
   .message-tab.active {
       background-color: #03C75A;
       color: white;
       box-shadow: 0 4px 12px rgba(3, 199, 90, 0.3);
   }
   ```

3. **토스트 애니메이션**
   ```css
   @keyframes slideInUp {
       from { transform: translateY(100px); opacity: 0; }
       to { transform: translateY(0); opacity: 1; }
   }
   ```

4. **영업 단계 드롭다운 스타일**
   ```css
   .business-card select:hover {
       border-color: #3B82F6;
       background-color: #F0F9FF;
   }
   ```

---

## 📌 다음 단계 (Backend 작업)

### 필수 작업:
1. `messages.fifth` 생성 로직 추가
   - 결과 페이지 렌더링 함수에서 구현
   - 계약 의향 단계에서만 생성

2. `sales_stage` 데이터베이스 컬럼 추가
   ```sql
   ALTER TABLE history ADD COLUMN sales_stage VARCHAR(20) DEFAULT '미접촉';
   CREATE INDEX idx_sales_stage ON history(sales_stage);
   ```

3. Sales Stage 업데이트 엔드포인트 추가
   ```python
   @app.patch('/api/businesses/{history_id}/sales-stage')
   async def update_sales_stage(history_id: int, body: dict):
       # sales_stage 업데이트
       # localStorage 와 DB 동기화
   ```

### 선택사항:
1. Sales Stage 필터링 추가 (history.html)
   ```
   필터탭: 전체 / 미접촉 / 1차 / 2차 / 3차 / 4차 / 계약완료 / 거절
   ```

2. 영업 파이프라인 대시보드
   ```
   상태별 업체 수 통계 추가
   - 미접촉: N개
   - 1차발송: N개
   - 계약완료: N개
   ```

---

## 🧪 테스트 체크리스트

- [ ] result.html 로드 시 "비대면 영업 플로우 안내" 표시 확인
- [ ] 메시지 탭 클릭 시 정상 전환 확인
- [ ] 메시지 복사 시 토스트 알림 표시 확인
- [ ] history.html 영업 단계 드롭다운 선택 확인
- [ ] 새로고침 후 선택값 유지되는지 확인
- [ ] 모바일(375px) 화면에서 탭 레이아웃 확인
- [ ] 5차 탭 클릭 시 "아직 생성되지 않음" 메시지 표시 확인

---

## 📂 변경 파일 목록

1. `templates/result.html` — 메시지 탭 + 5차 탭 + 플로우 안내
2. `templates/history.html` — 영업 단계 드롭다운
3. `static/js/message_tabs.js` — 복사 피드백 개선 + 토스트 알림
4. `static/js/history_filter.js` — 영업 단계 저장 함수 추가
5. `static/css/style.css` — 메시지 탭 + 토스트 + 드롭다운 스타일

---

## 📞 문의
Frontend 파트 개선사항 관련 질문은 이 파일을 참고하세요.

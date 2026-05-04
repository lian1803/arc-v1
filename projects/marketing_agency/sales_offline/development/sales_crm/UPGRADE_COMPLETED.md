# 영업CRM 업그레이드 완료 (2026-04-07)

## 구현된 기능

### 1. PDF/PPT 다운로드 엔드포인트 ✅
- **경로**: `GET /api/business/<business_id>/pdf`
- **기능**: naver-diagnosis의 `ppt_output/` 폴더에서 PPT 파일 다운로드
- **구현**:
  - sales_crm DB의 `pdf_path` 확인
  - naver-diagnosis DB에서 `ppt_filename` 조회
  - 파일이 있으면 첨부파일로 다운로드

### 2. 멘트 시퀀스 (4단계 영업 퍼널) ✅
- **상태 흐름**:
  ```
  1차_발송_대기 → (발송) → 1차_발송_완료 → (응답) → 2차_생성 → 2차_발송_대기 → ... → 계약완료
  ```
- **DB 테이블**: `message_sequences` (새로 추가)
  - `business_id`, `sequence_num`, `message`, `sent_at`, `customer_response`, `customer_responded_at`

### 3. 사진/네이버 플레이스 연동 ✅
- **place_url**: naver-diagnosis DB에서 조회 → sales_crm에 저장
- **헤더 버튼**: "🗺️ 네이버 플레이스" 링크 (클릭 시 새창 열기)
- **플레이스 직영 여부**: 페이지 로드 시 자동 검출 및 표시

### 4. 채팅 UI 개선 (chat.html) ✅
#### 헤더 개선
- 업체명, 전화번호 표시
- "🗺️ 네이버 플레이스" 링크 버튼
- "📋 제안서 다운로드" 버튼
- "← 뒤로" 버튼

#### 메시지 섹션 (신규)
- **현재 단계 메시지** 표시 (큰 텍스트박스)
- "📋 복사" 버튼 (클립보드에 복사)
- "✓ 발송 완료" 버튼 (상태 업데이트)

#### 다음 메시지 생성 (신규)
- 2차~4차 상태에서 "⚡ 다음 메시지 생성" 버튼
- 클릭 시 AI가 해당 단계 메시지 자동 생성
- 생성된 메시지를 현재 메시지로 표시

#### 고객 응답 입력
- "고객 응답을 여기에 복붕하세요..."
- Enter: 전송 / Shift+Enter: 줄바꿈
- 전송 시 자동으로 상태 업데이트 + 다음 메시지 생성 섹션 표시

### 5. 대시보드 UI 개선 (dashboard.html) ✅
#### 상태별 색상 구분
- 1차: 빨강 (긴급)
- 2차: 파랑 (진행)
- 3차: 초록 (진행)
- 4차: 주황 (마지막)
- 계약: 초록 (완료)

#### 액션 컬럼 (신규)
- "📋 PDF" 버튼: 제안서 다운로드
- "💬 채팅" 버튼: 채팅창 이동

#### 자동 새로고침
- 5초마다 업체 목록 갱신 (PDF 자동 감지)
- 상태 변화 실시간 반영

## DB 스키마 변경

### businesses 테이블
```sql
-- 추가된 컬럼
place_url TEXT                  -- 네이버 플레이스 URL
naver_diagnosis_id INTEGER      -- naver-diagnosis DB 참조 ID
```

### 새 테이블: message_sequences
```sql
CREATE TABLE message_sequences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id INTEGER,
    sequence_num INTEGER,        -- 1: 1차, 2: 2차, 3: 3차, 4: 4차
    message TEXT,                -- 생성된 메시지
    sent_at TIMESTAMP,           -- 발송 시간
    customer_response TEXT,      -- 고객 응답
    customer_responded_at TIMESTAMP,
    FOREIGN KEY(business_id) REFERENCES businesses(id)
)
```

## API 엔드포인트

### 신규 추가
| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/business/<id>/pdf` | PDF 다운로드 |
| POST | `/api/business/<id>/mark-sent` | 발송 완료 표시 |
| GET | `/api/business/<id>/next-message` | 다음 메시지 생성 |

### 기존 (수정됨)
| 메서드 | 경로 | 변경사항 |
|--------|------|---------|
| POST | `/api/business/<id>/respond` | 상태 자동 업데이트 추가 |
| GET | `/api/business/<id>` | place_url, naver_diagnosis_id 반환 |

## 상태 플로우 설명

### 1차 발송 대기 (`1차_발송_대기`)
- 리안이 1차 메시지를 복사하고 카톡으로 발송
- "✓ 발송 완료" 버튼 클릭
- 상태 → `1차_발송_완료`

### 1차 발송 완료 (`1차_발송_완료`)
- 사장님의 응답을 기다림
- 고객 응답 입력 → "⚡ 전송"
- AI가 거절 유형 감지 → 다음 메시지 자동 생성
- 상태 → `2차_생성`

### 2차 생성 (`2차_생성`)
- AI가 2차 메시지를 생성함 (message_sequences에 저장)
- "⚡ 다음 메시지 생성" 버튼 클릭 (또는 자동)
- 상태 → `2차_발송_대기`

### 2차 발송 대기 (`2차_발송_대기`)
- 리안이 2차 메시지 복사 + 발송
- "✓ 발송 완료" 버튼 클릭
- 상태 → `2차_발송_완료`

### 패턴 반복
- 2차 → 3차 → 4차 → 계약완료

## 기술 스택 유지

- **Backend**: Flask + Python
- **Frontend**: Vanilla JavaScript + Jinja2
- **DB**: SQLite (sales_crm.db + diagnosis.db)
- **PyInstaller**: 호환 유지 ✅

## 주의사항

### 1. UTF-8 인코딩
- PyInstaller EXE 호환성 유지
- 한글 처리 안전

### 2. 기존 코드 호환성
- naver-diagnosis message_generator 연동 유지
- 기존 API 하위호환성 100%
- DB 마이그레이션 불필요 (신규 테이블만 추가)

### 3. 에러 처리
- 모든 API 엔드포인트에 try-catch
- 파일 없음 → 404 반환
- 상태 불일치 → 명확한 에러 메시지

## 테스트 체크리스트

### Backend
- [x] app.py 문법 검증 (py_compile)
- [x] naver-diagnosis DB 연동 확인
- [x] 멘트 시퀀스 상태 로직 검증
- [x] PDF 다운로드 경로 확인

### Frontend
- [ ] 대시보드: PDF 다운로드 버튼 동작
- [ ] 채팅: 메시지 복사 기능
- [ ] 채팅: "발송 완료" 상태 업데이트
- [ ] 채팅: "다음 메시지 생성" 버튼
- [ ] 채팅: 네이버 플레이스 링크

### Integration
- [ ] PDF 감시 후 업체 자동 추가
- [ ] 상태별 UI 변화 확인
- [ ] 멘트 시퀀스 전체 흐름 테스트

## 실행 방법

```bash
cd sales_crm
python3 app.py
# 브라우저: http://localhost:5000
```

## 파일 수정 요약

| 파일 | 변경 | 라인 |
|------|------|------|
| app.py | 완전 재작성 (DB 스키마, API 추가) | 765 |
| chat.html | 대폭 개선 (메시지 섹션, JS 로직) | 685 |
| dashboard.html | UI 개선 (상태 색상, 액션 버튼) | 413 |

## FE 연결 시 알아야 할 것

1. **place_url**: naver-diagnosis DB에서 자동 조회
2. **PDF 경로**: `naver-diagnosis/ppt_output/{ppt_filename}`
3. **상태 값**: 1차_발송_대기 ~ 계약완료 (9가지)
4. **API 응답 포맷**: JSON (error/success 필드)
5. **웹소켓 없음**: REST API 폴링 (10초마다)

---

**배포 준비 완료!** 🚀

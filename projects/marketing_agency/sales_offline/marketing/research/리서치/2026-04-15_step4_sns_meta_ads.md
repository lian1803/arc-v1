# 4차 서칭: 메타 광고 대행 > 3개 소분류 심화
조사일: 2026-04-15
서칭 단계: 4/N

---

## A. 매장 방문(로컬 도달) 심화

### A-1. 반경(거리) 기반 로컬 타겟 광고 대행

- 한 줄 정의: 매장 주소를 기준으로 반경 1~50km 범위 내 사용자에게만 노출되는 위치 고정형 광고 대행
- 타겟 방식: 메타 광고 관리자 위치 설정에서 특정 주소 핀 + 반경(km/mile) 지정. 매장 위치를 Meta Business 위치 자산에 등록 후 "매장 위치 기능"으로 광고 세트 구성
- 목표 행동: 지도 앱 연동 길찾기 클릭, 전화 통화 버튼, 웹사이트 방문. CTA를 "길찾기 받기" 또는 "전화하기"로 고정
- 측정 방식: 클릭 수(링크/전화/길찾기) 기준. 2025년 5월 기존 Offline Conversions API 폐기 후 매장 실방문 추정치는 표준 CAPI + Signals Gateway 조합으로 대체. 단, 소규모 매장은 CAPI 연동 비용 문제로 클릭 수 + 수기 방문 카운트 병행이 현실적
- 업종: 헬스장, 필라테스, 카페, 학원, 미용실, 네일샵. 단일 매장·지역 고착형 업종에 적합. 다점포 체인은 A-2 복수 위치 상품으로 분기
- 출처 URL:
  - https://www.facebook.com/business/help/956093091134327
  - https://inside.ampm.co.kr/insight/13952
  - https://openads.co.kr/content/contentDetail?contsId=19094
- SKU 여부: **SKU 확정** — "반경 타겟 로컬 광고 월 운영 패키지"로 단독 상품화 가능. 설정 범위(반경 거리값)와 지역 수(단일/복수 매장)에 따라 단가 분기. 경쟁사 랜딩페이지 "지역 광고" 항목으로 이미 독립 노출 확인

---

### A-2. 복수 매장 위치 자산 기반 광고 대행

- 한 줄 정의: 2개 이상 매장 위치를 Meta Business Location Asset에 등록하고, 사용자 위치에 따라 가장 가까운 지점을 자동 매칭해 노출하는 다점포 전용 대행
- 타겟 방식: Meta Business Suite 위치 자산 등록(지점별 주소/운영 시간) → 광고 세트에서 "매장 위치" 기능 활성화 → 사용자 현재 위치와 가장 가까운 지점 자동 연결
- 목표 행동: 지점별 전화·길찾기·예약 CTA 자동 분기
- 측정 방식: 지점별 CTA 클릭 수 분리 리포팅. 위치 자산 설정 완료 매장에 한해 Meta 추정 매장 방문 지표(Store Visit Lift) 제공 — 단, 국내 소규모 자영업자에게는 데이터 신뢰도 논란 있음
- 업종: 프랜차이즈 가맹점주, 지역 체인 학원, 멀티 지점 헬스클럽
- 출처 URL:
  - https://about.fb.com/ko/news/2016/06/facebook%EC%9C%BC%EB%A1%9C-%EA%B3%A0%EA%B0%9D%EC%9D%98-%EB%A7%A4%EC%9E%A5-%EB%B0%A9%EB%AC%B8%EA%B3%BC-%EC%98%A4%ED%94%84%EB%9D%BC%EC%9D%B8-%EB%A7%A4%EC%B6%9C%EC%9D%84-%EB%8A%98%EB%A6%B4-%EC%88%98/
  - https://www.i-boss.co.kr/ab-3208-1700
- SKU 여부: **SKU 확정** — 단일 매장 패키지(A-1)와 다점포 패키지(A-2)는 위치 자산 세팅 공수 차이로 단가 분기 정당화. A-1 기본 → A-2 추가 지점 수 기반 과금 구조가 에이전시 표준

---

### A-3. 위치 관심(Location Interest) 기반 광고 대행

- 한 줄 정의: 실거주지/직장 반경이 아닌 "최근 해당 지역에 방문했거나 관심 보인 사람"을 타겟으로 하는 행동 기반 위치 광고 대행
- 타겟 방식: 메타 위치 설정 옵션 중 "이 위치에 사는 사람" 대신 "이 위치에 있었던 최근 방문자" 또는 "이 위치에 관심 있는 사람" 선택. 관광지 주변 맛집, 역세권 매장에 유효
- 목표 행동: 클릭 → 네이버 플레이스 이동, 예약 페이지 이동, 인스타 DM
- 측정 방식: 클릭 기준 (픽셀 미설치 매장은 링크 클릭 + UTM 파라미터 추적)
- 업종: 관광지 인근 카페·맛집, 쇼핑몰 주변 뷰티 매장, 역 앞 학원 등 유동 인구 의존형 업종
- 출처 URL:
  - https://inside.ampm.co.kr/insight/13952
  - https://www.i-boss.co.kr/ab-6141-69508
- SKU 여부: **SKU 확정** — 반경 고정형(A-1)과 구분되는 별도 상품. "유동인구 타겟 광고"로 별도 명칭화해 랜딩에 올릴 수 있음

---

### A-4. 매장 방문 전환 측정 세팅 대행 (CAPI + Signals Gateway)

- 한 줄 정의: 2025년 5월 기존 Offline Conversions API 폐기 이후, 표준 CAPI 또는 Signals Gateway를 통해 오프라인 방문·전화·예약 데이터를 메타 알고리즘에 송신하는 기술 세팅 단독 상품
- 타겟 방식: 해당 없음(측정 인프라 구축 상품)
- 측정 방식: CAPI → Meta 서버로 매장 방문/전화/CRM 리드 이벤트 직접 전송. Signals Gateway 추가 시 온·오프라인 시그널 통합 파이프라인 구성 → 평균 CPA 추가 개선 효과 보고됨
- 업종: 전환 캠페인 또는 로컬 캠페인을 집행 중인 모든 오프라인 매장 (기술 세팅이 있어야 A-1~A-3 성과 측정이 가능)
- 출처 URL:
  - https://openads.co.kr/content/contentDetail?contsId=19094
  - https://blog.ab180.co/posts/facebook-conversion-api-1
  - https://www.i-boss.co.kr/ab-6141-67960
- SKU 여부: **SKU 확정** — 2025년 5월 구API 폐기 이후 독립 상품화 논거 생김. "CAPI 세팅 대행 (원타임)" + "월 유지 관리" 2단계 과금 구조 가능. 픽셀·CAPI 병행 설치 + EMQ 점수 최적화까지 묶으면 하나의 독립 상품

---

## B. 전환 캠페인 심화

### B-1. 네이버 예약·톡톡 연동 전환 캠페인 대행

- 한 줄 정의: 메타 광고 클릭 → 네이버 예약 페이지 또는 네이버 톡톡으로 랜딩시켜 예약·상담 전환을 측정하는 캠페인 대행
- 전환 지점: 네이버 예약(스마트 예약), 네이버 톡톡 DM 오픈, 네이버 플레이스 링크 클릭
- 최적화 목표: 링크 클릭 + UTM → 네이버 예약 완료 수동 카운트. 메타 픽셀 직접 설치 불가 → 클릭 기반 간접 측정. 예약 완료 데이터를 CAPI로 수동 업로드하는 방식이 2026년 현장 대응 표준
- 픽셀·CAPI 포함 여부: 픽셀 미설치(네이버 도메인 제한) + CAPI 수동 업로드 구조. 이를 설계·운영하는 것이 대행사 핵심 공수
- 업종: 미용실, 피부관리실, 헬스장, 병원, 학원 — 네이버 예약 사용 오프라인 매장 전체
- 출처 URL:
  - https://inside.ampm.co.kr/insight/13161
  - https://openads.co.kr/content/contentDetail?contsId=19094
  - https://1point.kr/blog/insights/meta-tracking/
- SKU 여부: **SKU 확정** — "네이버 예약 연동 전환 캠페인"으로 이미 독립 상품화된 사례 복수 확인. 픽셀 직설치가 불가한 네이버 환경 특성상 설계·운영 난도가 높아 일반 전환 캠페인과 분리 판매 정당화

---

### B-2. 자사 예약 페이지·아임웹 결제 전환 캠페인 대행 (픽셀+CAPI 포함)

- 한 줄 정의: 자사몰(아임웹, 카페24, 큐샵 등) 또는 자체 예약 페이지에 픽셀·CAPI 직접 설치 후 구매·예약 전환 최적화 캠페인 대행
- 전환 지점: 아임웹 결제 완료, 카페24 구매 완료, 자체 폼 제출(시술 예약, 수강 신청)
- 최적화 목표: Purchase / CompleteRegistration / Lead 이벤트 기준 캠페인 최적화. EMQ 점수 8.0 이상 유지가 ROAS 안정화 핵심
- 픽셀·CAPI 포함 여부: **포함 세팅이 핵심 공수** — 픽셀 단독 시 전환 데이터 40% 유실. CAPI 병행 설치 시 서버사이드 이중 전송으로 복원. 아임웹·카페24는 공식 메타 CAPI 파트너로 설정 간소화 가능
- 업종: 온라인 예약 도입 오프라인 매장 전체. 특히 시술권·수강권·식품 판매 매장
- 출처 URL:
  - https://openads.co.kr/content/contentDetail?contsId=19094
  - https://www.datarize.ai/blog/metaguide
  - https://blog.ab180.co/posts/facebook-conversion-api-1
  - https://imweb.me/faq?mode=view&category=29&category2=47&idx=71239
- SKU 여부: **SKU 확정** — B-1(네이버 간접 측정)과 B-2(자사 직설치)는 기술 구성·공수·측정 정확도가 완전히 다름. 대행사들이 상품 분리 판매 중

---

### B-3. 인스타 DM 전환(리드 수집) 캠페인 대행

- 한 줄 정의: 광고 클릭 → 인스타그램 DM 오픈 → 상담·예약 리드 수집을 전환 목표로 설정한 캠페인 대행. 별도 랜딩 페이지 없이 DM으로 직결
- 전환 지점: 인스타 DM 대화 시작 (Messaging 캠페인 목표 또는 전환 캠페인에서 DM CTA)
- 최적화 목표: 메시지 시작 수(Messaging Conversations Started) 기준 최적화
- 픽셀·CAPI 포함 여부: 픽셀 불필요. 메타 내부 이벤트로 전환 측정 자체 처리. 랜딩 페이지 세팅 비용 없어 소규모 매장 진입 장벽 낮음
- 업종: 1인 뷰티샵, 소형 학원, 인테리어·리모델링 업체, 펫샵 등 전화/DM 상담 중심 업종
- 출처 URL:
  - https://inside.ampm.co.kr/insight/12648
  - https://www.i-boss.co.kr/ab-6141-69508
- SKU 여부: **SKU 확정** — "DM 상담 전환 캠페인" 단독 상품으로 랜딩에 올라가 있는 대행사 복수 확인. 랜딩 불필요 → 세팅 난도 낮음 → 소규모 자영업 입문용 상품으로 포지셔닝 가능

---

### B-4. 전화 전환 캠페인 대행 (Click-to-Call)

- 한 줄 정의: 광고 CTA를 "전화하기"로 설정해 클릭 즉시 통화 연결을 유도하는 캠페인 대행. 전화 예약·문의가 주 채널인 업종 특화
- 전환 지점: 광고 내 전화 버튼 클릭 → 즉시 통화
- 최적화 목표: 전화 클릭 수 기준. 메타 광고 관리자 내 통화 클릭 이벤트 자동 집계
- 픽셀·CAPI 포함 여부: 불필요. 메타 내부 이벤트로 측정
- 업종: 병원, 한의원, 법률 사무소, 인테리어, 이사업체, 자동차 수리 — 전화 상담이 계약 첫 단계인 업종
- 출처 URL:
  - https://www.facebook.com/business/help/956093091134327
  - https://inside.ampm.co.kr/insight/12648
- SKU 여부: **SKU 확정** — 별도 CTA 세팅과 측정 구조. B-3(DM) vs B-4(전화) 분리는 업종 특성에 따른 실질적 상품 차이

---

## C. 릴스 광고 심화

### C-1. 실사 촬영 릴스 광고 소재 제작 + 집행 대행

- 한 줄 정의: 촬영 기획·현장 촬영·편집·광고 집행을 묶은 원스톱 패키지. 소재 제작과 광고 운영을 분리하지 않고 통합 판매
- 소재 포맷: 9:16 세로 영상, 15~30초 권장. 인물 중심 오가닉 형태 유지. CTA 버튼·네비게이션 데드존(상하단) 회피 구성
- 업종별 포맷:
  - 뷰티·피부시술: 시술 전후(Before/After) 10~15초. 얼굴 클로즈업 중심. 리뷰어 UGC 형식
  - 맛집·카페: 메뉴 제조 과정 + 완성 클로즈업. 15~20초. 소리(ASMR) 포함 — 릴스 이용자 75% 소리 켜고 시청
  - 헬스장·필라테스: 공간 투어 + 트레이너 시연. 15~30초
  - 학원: 수업 장면 + 수강생 인터뷰 짧게. 15~20초
- 광고 소재 제작 포함 여부: **포함** (이것이 C-1의 핵심 가치)
- 출처 URL:
  - https://www.simpact.co.kr/
  - https://inside.ampm.co.kr/insight/11941
  - https://inside.ampm.co.kr/insight/13391
  - https://www.mobiinside.co.kr/2025/02/25/creative-diversification-2/
- SKU 여부: **SKU 확정** — 제작 포함/미포함이 가장 큰 가격 분기점. "촬영+편집+집행" 통합 패키지는 이미 독립 상품으로 대행사 랜딩에 게시됨

---

### C-2. 템플릿 기반 릴스 광고 소재 제작 + 집행 대행

- 한 줄 정의: 기존 사장님 보유 사진·영상에 모션 템플릿을 적용해 릴스 소재를 제작하는 저비용 패키지. 촬영 없이 진행 가능
- 소재 포맷: 기존 이미지/영상 → 캡컷·Canva·메타 내장 AI 편집 도구로 9:16 릴스 변환. 자막 + BGM + 전환 효과 추가
- 광고 소재 제작 포함 여부: **포함** (단, 원본 소재는 클라이언트 제공)
- 업종별 포맷: 메뉴 사진이 있는 맛집, 시술 사진이 있는 뷰티샵, 상품 이미지가 있는 소매점
- 출처 URL:
  - https://inside.ampm.co.kr/insight/13391
  - https://www.mobiinside.co.kr/2025/02/25/creative-diversification-2/
  - https://nerdboard.kr/blog/meta-2026-creative-best-practices
- SKU 여부: **SKU 확정** — C-1(풀 제작)보다 저가 상품. "소재 있는 분 전용 패키지"로 별도 포지셔닝 가능. 진입 장벽을 낮추는 프론트엔드 상품

---

### C-3. AI 생성 릴스 광고 소재 + 집행 대행

- 한 줄 정의: fal.ai, Kling 등 AI 영상 생성 도구로 실사 촬영 없이 광고용 릴스 소재를 생성·편집 후 집행하는 신규 상품
- 소재 포맷: AI 생성 이미지 → AI 영상화 → 자막·CTA 추가. 실사와 구분 어려운 수준까지 가능(2026년 기준 Kling/Veo2)
- 광고 소재 제작 포함 여부: **포함**
- 업종별 포맷: 음식 플레이팅 영상(AI), 공간 인테리어 시뮬레이션, 제품 360도 뷰
- 출처 URL:
  - https://blog.highoutputclub.com/meta-business-trends-2026/
  - https://inside.ampm.co.kr/insight/13391
- SKU 여부: **SKU 조건부 확정** — 2026년 현재 일부 대행사가 실험적 상품으로 운영 중. 독립 메뉴 게시 사례 증가 추세이나 아직 표준화 단계. 소재 품질 QA 프로세스 구축이 선행 조건

---

### C-4. 6초 숏 릴스 광고 집행 대행 (소재 미포함)

- 한 줄 정의: 이미 보유한 소재를 6초 이내로 편집해 인지도·도달 목적으로 집행하는 경량 패키지
- 소재 포맷: 6초 이하. 오프닝 0.5초 안에 훅 필수 — "0.5초의 승부" 원칙 (ampm 인사이트)
- 광고 소재 제작 포함 여부: **미포함** (편집 경량 작업만)
- 업종별 포맷: 신메뉴 런칭 티저, 프로모션 공지, 이벤트 카운트다운
- 출처 URL:
  - https://alph.kr/blog/2025%EB%85%84-%EB%B0%9D%ED%98%80%EC%A7%84-%EB%A9%94%ED%83%80-%EA%B4%91%EA%B3%A0%EC%9D%98-%EC%A7%84%EC%8B%A4-%EC%A1%B0%ED%9A%8C%EC%88%98%EC%97%90-%EB%94%B0%EB%9D%BC-%EB%A6%B4%EC%8A%A4-%ED%99%94/
  - https://inside.ampm.co.kr/insight/13391
- SKU 여부: **SKU 조건부 확정** — 소재 미포함 경량 패키지. 단가가 낮아 독립 상품화 여부는 에이전시 상품 전략에 따라 다름. 기존 운영 고객 추가 판매용(업셀)으로 적합

---

## 5차 필요 여부

| 항목 | 5차 필요 여부 | 이유 |
|------|--------------|------|
| A. 매장 방문(로컬 도달) | **불필요** | 타겟 방식 4가지(반경/다점포/관심/CAPI세팅) 심화 완료. 실무 기준 SKU 전체 확인 |
| B. 전환 캠페인 | **부분 필요** | 네이버·DM·전화·자사몰 전환 지점 완료. 단, "Advantage+ 쇼핑 캠페인(ASC) + 전환 조합"이 2026 핵심 이슈 → 별도 심화 가치 있음 |
| C. 릴스 광고 | **불필요** | 소재 포맷(실사/템플릿/AI/6초) 4분류 + 제작 포함/미포함 분기 완료 |

---

## 조사 메모

- **2025-05 오프라인 전환 API 폐기 이후 현장 대응**: 기존 Offline Conversions API → 표준 CAPI + Signals Gateway로 통합. 소규모 자영업자는 CAPI 직설치 비용 문제로 클릭 기반 간접 측정 + 수기 방문 카운트 병행이 현실적 운영 방식. 이 전환 세팅을 대신해주는 것 자체가 독립 상품(A-4) 근거.

- **예상 밖 발견 1**: 인스타그램 라이브 광고가 2026년 3월 한국 정식 롤아웃됨. 오프라인 매장 라이브 커머스 + 광고 결합 상품이 신규 SKU로 부상 가능. 현재 3차 소분류에 미포함 — 5차 후보.

- **예상 밖 발견 2**: 매장 방문 캠페인에서 "Store Visit Lift" 측정치 신뢰도가 국내 소규모 자영업자 사이에서 논란. 실제 방문 추정치가 과대계상된다는 현장 의견 다수. 에이전시가 KPI 설정 시 클릭 기준으로 제안하는 것이 클레임 방어에 유리.

- **픽셀·CAPI 세팅이 독립 상품화되는 지점**: 네이버 예약 연동(직설치 불가 → 수동 CAPI 업로드 설계)과 2025년 5월 구API 폐기(기존 세팅 전면 재설계 필요)가 결합되면서 "측정 인프라 구축" 자체가 별도 원타임 과금 상품으로 자리잡는 흐름 명확. 이미 일부 대행사가 "전환 세팅 대행" 항목을 초기 계약에 분리 청구 중.

- **릴스 2026 핵심 인사이트**: Z세대 85%가 릴스 시청 후 브랜드 팔로우, 80%가 실제 구매로 이어짐. 오프라인 매장에서 릴스가 "발견 → 관심 → 방문/예약" 풀퍼널로 작동하는 유일한 포맷으로 확인. 6초 숏폼보다 15~30초 실사 소재가 전환 효율 더 높다는 현장 데이터 복수 확인.

---

## 출처 목록 (주요)

- https://www.facebook.com/business/help/956093091134327
- https://inside.ampm.co.kr/insight/13952
- https://inside.ampm.co.kr/insight/12648
- https://inside.ampm.co.kr/insight/11941
- https://inside.ampm.co.kr/insight/13391
- https://openads.co.kr/content/contentDetail?contsId=19094
- https://www.datarize.ai/blog/metaguide
- https://blog.ab180.co/posts/facebook-conversion-api-1
- https://1point.kr/blog/insights/meta-tracking/
- https://inside.ampm.co.kr/insight/13161
- https://www.i-boss.co.kr/ab-6141-69508
- https://www.i-boss.co.kr/ab-3208-1700
- https://www.i-boss.co.kr/ab-6141-67960
- https://blog.highoutputclub.com/meta-business-trends-2026/
- https://www.mobiinside.co.kr/2025/12/05/meta-2026-business-trend/
- https://www.mobiinside.co.kr/2025/02/25/creative-diversification-2/
- https://www.simpact.co.kr/
- https://raonhajekorea.com/
- https://alph.kr/blog/2025%EB%85%84-%EB%B0%9D%ED%98%80%EC%A7%84-%EB%A9%94%ED%83%80-%EA%B3%B5%EA%B3%A0%EC%9D%98-%EC%A7%84%EC%8B%A4-%EC%A1%B0%ED%9A%8C%EC%88%98%EC%97%90-%EB%94%B0%EB%9D%BC-%EB%A6%B4%EC%8A%A4-%ED%99%94/
- https://nerdboard.kr/blog/meta-2026-creative-best-practices
- https://www.roas-expert.com/ad/?uid=99&mod=document&pageid=1

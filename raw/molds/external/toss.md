# Toss — 한국 핀테크 UX 패턴

출처: Perplexity 5쿼리 (2026-04-29 검색). 주 1차 출처:
- toss.tech/article/8-writing-principles-of-toss (~2023, 카피 8원칙)
- toss.tech/article/signup (2021, 가입 흐름)
- toss.tech/article/tds-color-system-update (2023, 컬러)
- toss.tech/article/4-ways-for-minimum-input (2022.10, 클릭 최소화)
- yuni01.tistory.com SLASH22 (2022, 송금 예외)

## ICP — 이 패턴 쓸 빌더
한국 일반 사용자 + 자영업자(정수민 포함) 대상 모바일 앱 빌더. Toss 사용자 = MAU 1,437만 (2022.10 기준). ARC v2 test_run_001 정수민 SaaS 직접 차용 후보.

## 1. 인증 흐름
### 신규 가입 (총 5-10탭)
- 인트로 스킵(0-1) → 권한 허용(1-2) → 본인인증(이름/주민번호 앞자리/휴대폰/통신사 = 3-5탭) → 약관 동의(1-2)
- 입력 UI = 역순 입력으로 스크롤 최소화 (toss.tech/article/signup, 2021 개선)
### 로그인 (1-5탭, 자동로그인 시 0-1탭)
- 가입 후 "설정 > 보안"에서 PIN/패턴/생체(지문/얼굴) 활성화
- 자동 로그인 활성화 시 앱 실행만으로 즉시 진입

## 2. 온보딩
- 개인 사용자 첫 가치 도달 정확 클릭 수 [자료 부족 — Perplexity 1회 보강에서 specific X]
- 측정 효과: "1클릭당 1초 × MAU 1,437만 × 6개월 시간 절감" (toss.tech/4-ways-for-minimum-input, 2022.10)
- 핵심 원칙: "불필요한 클릭 최소화" + "Instant 온보딩"
- 카카오뱅크/케이뱅크 대비 비교 [자료 부족]

## 3. 한국어 카피 (8가지 라이팅 원칙, toss.tech/article/8-writing-principles-of-toss ~2023)
1. **Predictable hint** — 다음 화면 힌트. 예: "다른 곳에서 후불 결제 하기" → "내가 쓰는 브랜드 신청하기"
2. **Weed cutting** — 의미 없는 단어 제거. 예: "[앞으로] 받을 배당금" → "받을 배당금"
3. **Remove empty sentences** — 의미 없는 문장 제거
4. **Focus on key message** — 핵심 메시지만
5. **Easy to speak** — 말하듯 자연스럽게. 한자어/긴 호흡 X
6. **Suggest over force** — 권유 중심, 강요/공포 X
7. **Universal words** — 모두 이해, 무해
8. **Find hidden emotion** — 정보 + 감정 공감
- 추가: 해요체 / "-하기" 과다 X / 동사 중심 / 한 문장 한 메시지 (developers-apps-in-toss.toss.im/design/ux-writing.html)

## 4. 디자인 토큰
- **메인 컬러**: #3182F6 (브랜드 파랑, 2023 7년만 업데이트, toss.tech/article/tds-color-system-update)
- **글자 크기**: 토큰 추상화 (Typography 1, 2, 3...). Typography 1 = 기본 30sp (Android, tossmini-docs.toss.im)
- **버튼 높이 / 여백 / border-radius / 그리드** [자료 부족 — TDS 비공개 NPM 한정]

## 5. 예외 처리
- **네트워크 끊김**: "네트워크 연결이 불안정합니다. Wi-Fi와 LTE를 전환해보세요." 토스트/팝업 + 재시도 버튼 (earscoming.tistory.com, 2023)
- **입력 오류 (계좌번호 틀림)**: 입력 필드 하단 빨간 에러 텍스트 + 실시간 유효성 + 포커스 이동. 카피: "입력한 계좌번호가 올바르지 않습니다. 다시 확인해주세요." (toss.tech/article/21021, 2022)
- **송금 실패/타임아웃**: "이미 진행 중인 송금이 있습니다. 완료 후 재시도하세요." Kafka 기반 지연 처리 (SLASH22, 2022)
- **은행 점검**: "은행 점검 중입니다. 공지사항 확인 후 재시도하세요."
- **권한 거부 (카메라/알림/위치)** [자료 부족 — Toss specific X, 일반 가이드라인 추정만]
- 백엔드: @RestControllerAdvice 전역 예외 핸들러

## 가격 / 채널 / 결과
- 가격: 사용자 무료 (송금 무료가 핵심 유인). 수익 = B2B/광고/금융상품
- 채널 [자료 부족]
- MAU 1,437만 (2022.10). 2024-2026 최신 [자료 부족]

## ARC v2 차용 후보 (5)
1. **8가지 라이팅 원칙** → ARC 산출 한국어 UI 카피의 self-audit 체크리스트. 정수민 mock 버튼("예약 추가", "메모 저장")이 §5/§6 우연 통과 — 명시화 후 강제 가능.
2. **휴대폰 + PIN 2단계 인증** → 정수민 SaaS 인증 옵션 (B/C) 구체 단계 수 기준선 = 신규 5-10탭, 로그인 0-1탭. Clerk(추정 7-10탭) 비교 데이터.
3. **클릭 최소화 = 측정 가능한 시간 절감 ("1클릭 × MAU × 기간")** → ARC PLAN.md "Reach Gate 5분"의 측정 가능 게이트 보강 근거.
4. **에러 카피 = 구체 행동 제안** ("Wi-Fi와 LTE를 전환해보세요") → ARC 자동 에러 메시지 생성 시 차용. "확인" 같은 generic X.
5. **메인 컬러 #3182F6 (신뢰/금융 톤)** vs 정수민 mock 카카오 노랑 #FEE500 (친근/카톡 톤). 정수민 ICP에는 카카오 톤 유지 정합. **차용 X 근거 데이터**.

## 자료 부족
- 신규 가입/로그인 정확 클릭 수 (추정만)
- 온보딩 첫 가치 도달 화면 수 (개인 사용자)
- TDS 토큰 specific (버튼/여백/border-radius)
- 카카오뱅크/케이뱅크 대비 비교
- 권한 거부 카피 (Toss specific)
- 2024-2026 최신 데이터

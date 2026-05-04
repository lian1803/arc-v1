# 3차 소분류 — 데이터 분석 / 트래킹 서비스

> 조사일: 2026-04-15 | 조사자: 재원(jaewon)

---

## 1. GA4 기본 설치 및 계정 세팅

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| GA4 속성(Property) 생성 및 기본 설정 | GA4 계정 내 속성 생성, 보고 시간대·통화·비즈니스 정보 입력 | https://osoma.kr/ga-consulting/ |
| 웹 데이터 스트림 생성 및 측정 ID 발급 | 웹사이트용 데이터 스트림 생성, gtag 또는 GTM 연결을 위한 Measurement ID 발급 | https://osoma.kr/blog/ga4-start-settings/ |
| 향상된 측정(Enhanced Measurement) 활성화 | 스크롤 추적·외부 링크 클릭·사이트 내 검색·동영상 참여 자동 수집 설정 | https://osoma.kr/blog/ga4-start-settings/ |
| Google 신호 데이터(Google Signals) 활성화 | 교차 기기 추적 및 리마케팅 잠재고객 활용을 위한 신호 데이터 수집 활성화 | https://www.ascentkorea.com/ga4-initial-setting-guide/ |
| 데이터 보관 기간 14개월 설정 | 기본 2개월에서 14개월로 변경, 장기 분석 데이터 보관 환경 구성 | https://www.ascentkorea.com/ga4-initial-setting-guide/ |
| 내부 트래픽 필터 설정 | 회사 IP 및 개발자 트래픽을 제외하는 필터 등록으로 데이터 오염 방지 | https://osoma.kr/blog/ga4-start-settings/ |
| GA4 설치 검증 및 데이터 수집 확인 | DebugView·실시간 보고서로 태그 정상 작동 여부 최종 검증 | https://osoma.kr/ga-consulting/ |

---

## 2. GA4 커스텀 이벤트 설계 및 세팅

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 이벤트 측정 계획서(Tracking Plan) 작성 | 비즈니스 목표 기반으로 수집할 이벤트·파라미터 목록을 문서화 | https://www.mfitlab.com/solutions/blog/2023-05-31-productdataanalysis-beginner-trackingplan |
| 버튼 클릭 이벤트 태깅 | 핵심 CTA·메뉴·배너 클릭을 GTM 또는 gtag로 추적 이벤트 등록 | https://osoma.kr/blog/ga4-event/ |
| 폼 제출(Form Submit) 이벤트 세팅 | 문의·신청·가입 폼 제출 완료를 이벤트로 수집, 리드 전환 측정 기반 구성 | https://adall.kr/blog/b98b34ef-bc4d-4a1a-acfc-011458d11f23/ |
| 스크롤 깊이·페이지 체류 이벤트 설정 | 25/50/75/90% 스크롤 도달, N초 이상 체류 행동 이벤트 등록 | https://osoma.kr/blog/ga4-event/ |
| 맞춤 측정기준·측정항목(Custom Dimensions/Metrics) 등록 | 이벤트 파라미터를 보고서에서 분석 가능한 측정기준·항목으로 GA4에 등록 | https://osoma.kr/blog/ga4-dimension-metrics/ |
| 이벤트 수정·이벤트 생성(GA4 Event Modify) 활용 | GTM 없이 GA4 관리 화면에서 기존 이벤트 조건 수정 또는 신규 이벤트 파생 | https://analyticsmarketing.co.kr/digital-analytics/google-analytics-4/6008/ |
| 세그먼트 및 잠재고객(Audience) 생성 | 이벤트 기반으로 특정 행동 사용자 세그먼트 구성, 광고 리마케팅 연동 | https://osoma.kr/blog/ga4-segment/ |

---

## 3. GA4 전자상거래(E-commerce) 추적 세팅

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 상품 조회(view_item) 이벤트 세팅 | 상품 상세 페이지 진입 시 상품 ID·이름·가격 파라미터 수집 | https://osoma.kr/blog/ga4-ecommerce-metric-dimension/ |
| 장바구니 담기(add_to_cart) 이벤트 세팅 | 장바구니 추가 행동 및 상품 정보 이벤트 등록 | https://leadspot.co.kr/blog/googleanalytics4/gtm을-활용한-ga4-전자상거래-추적/ |
| 결제 진행(begin_checkout) 이벤트 세팅 | 결제 단계 진입 시 이벤트 수집, 결제 퍼널 분석 기반 구성 | https://www.exelient.co.kr/project/ga4-ecommerce-setting/ |
| 구매 완료(purchase) 이벤트 및 거래 데이터 세팅 | 거래 ID·매출액·수량 포함 구매 완료 이벤트 등록, 전환 값 기반 광고 최적화 연동 | https://dachata.com/google-analytics-4/post/ga4-enhanced-ecommerce-tagging/ |
| 상품 목록 조회(view_item_list) 및 클릭(select_item) 세팅 | 카테고리·검색 결과 상품 노출 및 클릭 추적, 상품별 노출 대비 전환 분석 | https://osoma.kr/blog/ga4-ecommerce-metric-dimension/ |
| 프로모션·쿠폰 추적(view_promotion / select_promotion) | 배너·이벤트 프로모션 노출·클릭 데이터 수집, 프로모션 효율 측정 | https://openads.co.kr/content/contentDetail?contsId=12668 |
| 고도몰·카페24·아임웹 등 플랫폼별 이커머스 세팅 | 쇼핑몰 플랫폼 특성에 맞게 DataLayer 또는 스크립트 커스터마이징 | https://beingguru.life/godomall-ga4-ecommerce-setting/ |

---

## 4. GA4 전환(Conversion) 목표 설정

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 핵심 이벤트(Key Event) 전환 지정 | 구매·신청·가입 등 비즈니스 목표 이벤트를 GA4 핵심 이벤트로 전환 설정 | https://adall.kr/blog/b98b34ef-bc4d-4a1a-acfc-011458d11f23/ |
| 전환 값(Conversion Value) 설정 | 전환별 매출 가치 할당, 광고 플랫폼 스마트 자동입찰 신호 최적화 | https://adall.kr/blog/b98b34ef-bc4d-4a1a-acfc-011458d11f23/ |
| Google Ads 전환 가져오기(Import) 연동 | GA4 전환을 Google Ads 전환으로 가져와 광고 입찰 최적화 신호로 활용 | https://analyticsmarketing.co.kr/digital-analytics/google-analytics-4/6008/ |
| 전환 창(Conversion Window) 설정 | 광고 클릭 후 전환 인정 기간 설정, 캠페인 성과 측정 기준 정의 | https://segama.co.kr/blog/24343/ |
| 마이크로 전환(Micro Conversion) 정의 및 등록 | 구매 전 중간 행동(스크롤 75%, PDF 다운로드 등)을 보조 전환으로 등록 | https://osoma.kr/ga-consulting/ |

---

## 5. GTM(구글 태그 매니저) 계정 구축 및 기본 태그 세팅

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| GTM 계정 및 컨테이너 생성 | GTM 계정 신규 생성, 웹/앱 컨테이너 구분 설정 및 관리자 권한 구성 | https://analyticsmarketing.co.kr/digital-analytics/google-tag-manager-basics/3165/ |
| GTM 스니펫 코드 웹사이트 삽입 | head/body 태그에 GTM 컨테이너 스니펫 삽입 및 정상 로딩 확인 | https://analyticsmarketing.co.kr/digital-analytics/google-tag-manager-basics/3386/ |
| GA4 기본 구성 태그 생성 및 배포 | GTM에서 GA4 Configuration Tag 생성 후 All Pages 트리거 연결, 게시 | https://occamdata.kr/blog/google-tag-manager/1353/ |
| 기본 트리거(All Pages, DOM Ready, Window Loaded) 구성 | 공통 트리거 세트 구성으로 추후 태그 추가 효율화 | https://analyticsmarketing.co.kr/digital-analytics/google-tag-manager-basics/3165/ |
| 내장 변수(Built-in Variables) 활성화 | 클릭 ID·URL·폼 ID 등 기본 내장 변수 활성화, 태깅 기반 구성 | https://community.heartcount.io/ko/gtm-ga4-event-tutorial/ |
| GTM 태그 미리보기(Preview) 및 QA 검증 | Preview 모드에서 태그 발동 순서·데이터 전송값 확인 후 최종 게시 | https://www.exelient.co.kr/project/from-ga4-setup-to-gtm-integration/ |

---

## 6. GTM 고급 태깅 (커스텀 이벤트·데이터레이어)

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| DataLayer 설계 및 구현 가이드 작성 | 개발팀 협업용 DataLayer 스펙 문서 작성, push 시점·변수명 정의 | https://www.openads.co.kr/content/contentDetail?contsId=5866 |
| DataLayer 변수(DataLayer Variable) 추출 설정 | GTM에서 DataLayer에 담긴 동적 값(상품명·가격·회원등급 등)을 변수로 추출 | https://openads.co.kr/content/contentDetail?contsId=14136 |
| 커스텀 이벤트(Custom Event) 트리거 생성 | 개발팀이 push한 DataLayer 이벤트명을 트리거로 등록, 태그 발동 조건 구성 | https://www.ascentkorea.com/create-custom-eventgtm-ga4/ |
| JavaScript 변수(Custom JavaScript Variable) 활용 | DOM 쿼리·쿠키·로컬스토리지 값을 JS 변수로 추출, 복잡한 조건 태깅 구현 | https://studiomx.co.kr/5012/ |
| 정규표현식(Regex) 조건 트리거 고급 설정 | URL 패턴·이벤트 파라미터 조건에 정규식 적용, 세밀한 트리거 제어 | https://analyticsmarketing.co.kr/digital-analytics/google-tag-manager-basics/3165/ |
| GTM 버전 관리 및 변경 이력 문서화 | 컨테이너 버전별 변경 내역 기록, 롤백 가능한 운영 환경 구성 | https://bizspring.co.kr/company/ga.php |

---

## 7. 메타 픽셀(Meta Pixel) 설치 및 표준 이벤트 세팅

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 픽셀 베이스 코드 설치 (GTM 또는 직접 삽입) | Meta Business Manager에서 픽셀 생성 후 GTM 통해 전 페이지 배포 | https://adall.kr/blog/1a7cecd7-aeeb-4fc6-b7e7-3bbb6c82d83d/ |
| PageView·ViewContent 표준 이벤트 세팅 | 페이지 조회 및 콘텐츠 상세 조회 표준 이벤트 등록 | https://ko-kr.facebook.com/business/help/402791146561655 |
| AddToCart·InitiateCheckout·Purchase 이벤트 세팅 | 장바구니·결제 시작·구매 완료 전환 이벤트 등록, 광고 최적화 신호 구성 | https://inside.ampm.co.kr/insight/4648 |
| Lead·CompleteRegistration 이벤트 세팅 | 리드 수집·회원가입 완료 이벤트 등록, 리드 캠페인 전환 측정 | https://adall.kr/blog/1a7cecd7-aeeb-4fc6-b7e7-3bbb6c82d83d/ |
| 이벤트 매칭 품질(EMQ) 개선 설정 | 이메일·전화번호 등 고객 식별 파라미터 추가로 이벤트 매칭률 향상 | https://www.facebook.com/business/help/2254103654917599 |
| 픽셀 이벤트 테스트 도구(Test Events) 검증 | Meta Events Manager 테스트 이벤트 탭에서 픽셀 수신 데이터 실시간 확인 | https://openads.co.kr/content/contentDetail?contsId=10204 |

---

## 8. 메타 전환 API(Conversions API, CAPI) 구축

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| CAPI 서버 직접 연동 구축 | 서버에서 Meta Graph API로 이벤트 전송하는 서버사이드 추적 환경 구성 | https://blog.ab180.co/posts/facebook-conversion-api-1 |
| GTM 서버 컨테이너 통한 CAPI 구축 | Server-Side GTM에서 Meta CAPI 태그 구성, 픽셀과 서버사이드 병행 운영 | https://dbcart.net/posting_facebook_conversion_api.html |
| 이벤트 중복 제거(Deduplication) 설정 | event_id 파라미터 설정으로 픽셀·CAPI 이중 수집 시 중복 집계 방지 | https://blog.ab180.co/posts/facebook-conversion-api-1 |
| 픽셀+CAPI 이벤트 매칭 점수 개선 | 양방향 데이터 통합으로 이벤트 매칭 품질(EMQ) 점수 향상 | https://experienceleague.adobe.com/ko/docs/experience-platform/tags/extensions/server/meta/overview |
| CAPI 연동 후 광고 성과 비교 분석 | CAPI 도입 전·후 전환 수 변화·ROAS 개선 효과 측정 보고 | https://blog.ab180.co/posts/facebook-conversion-api-1 |

---

## 9. 카카오 픽셀 / 카카오 모먼트 트래킹 세팅

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 카카오 픽셀 스크립트 기본 설치 | 카카오 비즈니스에서 픽셀 ID 발급 후 웹사이트 전 페이지 배포 | https://kakaobusiness.gitbook.io/main/tool/pixel-sdk |
| PageView·CompleteRegistration 이벤트 등록 | 페이지 조회·회원가입 완료 표준 이벤트 등록 | https://help.sixshop.com/learn-sixshop/store-manager/add-ons/kakao-pixel |
| Purchase·AddToCart 전환 이벤트 세팅 | 구매 완료·장바구니 담기 전환 이벤트 등록, 카카오모먼트 전환 최적화 연동 | https://kakaobusiness.gitbook.io/main/tool/pixel-sdk/linkage |
| 카카오 픽셀 SDK(앱) 연동 | 모바일 앱 내 카카오 픽셀 SDK 삽입, 앱 내 구매·이벤트 추적 | https://kakaobusiness.gitbook.io/main/tool/pixel-sdk |
| 카카오 모먼트 잠재고객(리타겟팅) 연동 | 픽셀 데이터 기반 맞춤타겟·유사타겟 생성, 카카오모먼트 광고 연결 | https://sonet.kr/2071/ |
| 픽셀 이벤트 정상 수집 여부 검증 | 카카오 비즈니스 픽셀 & SDK 대시보드에서 이벤트 수신 실시간 확인 | https://cs.kakao.com/helps_html/1073201145?locale=ko |

---

## 10. 네이버 광고 전환 추적 세팅

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 네이버 전환 추적 스크립트 발급 및 삽입 | 네이버 광고 관리 시스템에서 전환 추적 스크립트 생성 후 전환 페이지 배포 | https://dbcart.net/posting_naver_pixel.html |
| 구매·신청 전환 이벤트 등록 | 구매 완료·상담 신청 완료 URL 기반 전환 추적 설정 | https://naver.github.io/conversion-tracking/pages/02_ecom_platform_guide/ |
| 네이버 검색광고 전환 연동 확인 | 전환 추적 데이터가 네이버 광고 보고서에 정상 반영되는지 확인 | https://dbcart.net/posting_naver_pixel.html |
| 네이버 쇼핑 성과형 DA 전환 세팅 | 네이버 쇼핑 광고 전환 스크립트 추가 삽입 및 상품별 전환 데이터 연동 | https://kmong.com/gig/449053 |
| GTM을 통한 네이버 전환 스크립트 배포 | GTM 커스텀 HTML 태그로 네이버 전환 스크립트 중앙 관리 | https://kmong.com/gig/449053 |

---

## 11. 틱톡 픽셀 설치 및 이벤트 세팅

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 틱톡 픽셀 기본 설치 (GTM 또는 직접) | TikTok Ads Manager에서 픽셀 생성 후 웹사이트 배포 | https://kmong.com/gig/449053 |
| ViewContent·AddToCart 이벤트 세팅 | 상품 상세 조회·장바구니 담기 이벤트 등록 | https://kmong.com/gig/449053 |
| Purchase·CompleteRegistration 전환 이벤트 등록 | 구매 완료·가입 완료 전환 이벤트 등록, 틱톡 광고 최적화 연동 | https://kmong.com/gig/449053 |
| 틱톡 이벤트 API(서버사이드) 연동 | 쿠키 차단 환경 대응을 위한 서버 → 틱톡 직접 전환 데이터 전송 | https://kmong.com/gig/449053 |
| 픽셀 이벤트 검증 (TikTok Pixel Helper) | TikTok Pixel Helper 크롬 확장 도구로 이벤트 발동 및 파라미터 확인 | https://kmong.com/gig/449053 |

---

## 12. 구글 애즈 전환 태그 설치 및 전환 추적 세팅

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| Google Ads 전환 액션(Conversion Action) 생성 | Google Ads 계정에서 웹사이트 전환·전화 통화·앱 전환 액션 생성 | https://business.google.com/kr/ad-tools/conversion-tracking/ |
| GTM 통한 Google Ads 전환 태그 배포 | GTM에서 Google Ads 전환 추적 태그 생성, 전환 트리거 연결 후 배포 | https://analyticsmarketing.co.kr/digital-analytics/google-tag-manager-basics/3517/ |
| Google Ads 동적 리마케팅 태그 세팅 | 상품 ID 파라미터 포함 동적 리마케팅 태그 설치, 쇼핑 캠페인 연동 | https://support.google.com/tagmanager/answer/6105160?hl=ko |
| GA4 → Google Ads 전환 가져오기 설정 | GA4 핵심 이벤트를 Google Ads 전환으로 가져와 광고 입찰 최적화 활용 | https://imweb.me/faq?mode=view&category=29&category2=35&idx=72121 |
| 전환 추적 태그 검증 (Tag Assistant) | Google Tag Assistant로 전환 태그 발동 여부 및 전환 값 수신 확인 | https://support.google.com/google-ads/answer/7521212?hl=ko |
| 전환 창(Window) 및 계산 방식 설정 | 전환 인정 기간·모든 전환/유일 전환 계산 방식 설정 | https://segama.co.kr/blog/24343/ |

---

## 13. 구글 서치 콘솔(GSC) 연동 및 SEO 데이터 수집

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| GSC 소유권 인증 및 사이트 등록 | HTML 태그·DNS·Google Analytics 방식으로 소유권 인증 완료 | https://imweb.me/faq?mode=view&category=29&category2=35&idx=15573 |
| 사이트맵(Sitemap) 제출 | XML 사이트맵 생성 및 GSC 제출, 크롤링·색인 효율 개선 | https://www.hedleyonline.com/ko/blog/google-search-console/ |
| GA4 ↔ GSC 연동 설정 | GA4 속성에 GSC 연결, GA4 보고서 내 유기 검색 키워드 데이터 통합 | https://www.ascentkorea.com/seo-how-to-use-google-tool/ |
| Looker Studio ↔ GSC 연동 대시보드 구성 | GSC 데이터를 Looker Studio에 연결, 키워드·노출·클릭·순위 시각화 | https://datastorytelling.kr/lookerstudio-overview/ |
| Core Web Vitals 모니터링 설정 | GSC 핵심 웹 지표 보고서 확인, LCP·FID·CLS 개선 우선순위 파악 | https://segama.co.kr/blog/24322/ |
| 검색 쿼리·페이지별 CTR 분석 | 상위 노출 키워드·CTR 낮은 페이지 파악, 메타 타이틀·설명 개선 근거 도출 | https://www.ascentkorea.com/seo-how-to-use-google-tool/ |

---

## 14. Looker Studio(루커스튜디오) 대시보드 제작

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| GA4 ↔ Looker Studio 데이터 소스 연결 | GA4 속성을 Looker Studio에 연결, 자동 업데이트 보고서 기반 구성 | https://datastorytelling.kr/lookerstudio-overview/ |
| 광고 채널 통합 대시보드 제작 | Google Ads·Meta·카카오 데이터를 한 화면에서 확인하는 멀티채널 대시보드 | https://kmong.com/gig/566256 |
| 전환·매출 중심 KPI 대시보드 제작 | ROAS·CPA·CVR·매출 등 핵심 KPI 카드 배치, 기간 비교 차트 구성 | https://kmong.com/gig/516764 |
| 맞춤 계산 필드(Calculated Field) 설계 | Looker Studio 내 ROAS·CPL 등 파생 지표 공식 구성 | https://datastorytelling.kr/lookerstudio/ |
| 페이지별 자동 업데이트 리포트 구성 | 날짜 범위 컨트롤·필터 추가, 담당자가 직접 기간 설정 가능한 인터랙티브 보고서 | https://kmong.com/gig/516764 |
| Google Sheets 연동 커스텀 데이터 시각화 | 수동 데이터·CRM 데이터를 Google Sheets 경유 Looker Studio 반영 | https://seo.tbwakorea.com/blog/looker-studio-guide-part1/ |

---

## 15. 맞춤 BI 대시보드 제작 (Tableau / Power BI / Superset)

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 데이터 소스 연결 및 데이터 모델 설계 | DB·CSV·API·BigQuery 등 다양한 소스를 BI 툴에 연결, 관계 모델 설계 | https://aio.it.kr/page?no=1 |
| KPI 대시보드 화면 설계 및 제작 | 경영진·마케팅팀 용도별 KPI 화면 레이아웃 설계, 차트·표 배치 | https://elice.io/ko/newsroom/tableau_dashboard |
| 드릴다운(Drill-down) 인터랙티브 차트 구성 | 상위 집계 → 세부 데이터 탐색 가능한 인터랙티브 필터·계층 구조 구성 | https://www.tableau.com/ko-kr/learn/articles/business-intelligence |
| 마케팅 채널별 기여도 시각화 | 채널별 전환 기여도·ROAS·CLV 비교 시각화, 예산 배분 의사결정 지원 | https://bizspring.co.kr/data_intelligence.php |
| BI 대시보드 운영 교육 및 매뉴얼 제공 | 클라이언트 담당자가 직접 필터·기간 조작 가능하도록 사용 교육 진행 | https://community.heartcount.io/ko/big-5-bi-tool/ |

---

## 16. 정기 성과 리포팅 대행 (월간·주간)

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 주간 광고 성과 요약 리포트 | 채널별 노출·클릭·전환·광고비 주간 집계, 전주 대비 증감 분석 | https://www.igaworksblog.com/post/insight-반복되는-리포팅-업무와의-전쟁에서-이기는-리포트-자동화 |
| 월간 통합 성과 분석 리포트 | GA4·광고·CRM 데이터 통합, 월간 ROAS·CPA·CVR 추세 및 인사이트 제공 | https://www.studiobustles.com/sample_report |
| 광고 매체별 세부 성과 분석 | 캠페인·광고그룹·키워드·소재 단위까지 세분화한 매체별 성과 분석 | https://bizspring.co.kr/company/prd_air.php |
| 리포트 자동화 설정 (API 연동) | 광고 플랫폼 API 연동, 데이터 자동 수집·정형화·리포트 자동 발송 환경 구성 | https://bizspring.co.kr/company/prd_air.php |
| 인사이트 도출 및 다음 달 액션 아이템 제안 | 단순 데이터 나열이 아닌 성과 원인 분석 + 개선 액션 제안 포함 리포트 | https://www.ab180.co/ |
| Looker Studio 자동 업데이트 리포트 연동 | 클라이언트 공유 링크로 실시간 확인 가능한 자동 업데이트 대시보드 제공 | https://kmong.com/gig/328160 |

---

## 17. 마케팅 데이터 통합 파이프라인 구축

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 다채널 광고 데이터 API 연동 | Google Ads·Meta·카카오·네이버 광고 API를 단일 데이터 웨어하우스에 연결 | https://bizspring.co.kr/company/prd_air.php |
| ETL 파이프라인 설계 및 구축 | 데이터 추출(Extract)·변환(Transform)·적재(Load) 자동화 파이프라인 구성 | https://www.datamarketing.co.kr/ |
| 데이터 웨어하우스(BigQuery / Redshift) 환경 구축 | 마케팅 데이터 장기 보관 및 SQL 분석을 위한 클라우드 DW 환경 구성 | https://goldenplanet.co.kr/our_contents/blog?number=1013 |
| CRM·커머스 데이터 통합 연동 | 오프라인 CRM·쇼핑몰 DB를 광고 데이터와 통합, 온·오프라인 통합 분석 | https://www.datamarketing.co.kr/ |
| 데이터 정규화 및 스키마 설계 | 채널별 상이한 지표명·단위를 통일된 스키마로 정규화 | https://medium.com/myrealtrip-product/data-driven-marketing-시작하기-e82f66ff9c41 |

---

## 18. 유입 경로(Attribution) 분석 및 멀티터치 모델링

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 라스트 클릭 vs 데이터 기반 모델 비교 분석 | GA4 기본 어트리뷰션 모델별 전환 기여 차이 분석, 최적 모델 선정 | https://www.thedigitalmkt.com/guide-to-attribution-modeling/ |
| 멀티터치 기여도(MTA) 분석 | 전환 경로상 모든 터치포인트에 기여도 배분, 채널별 실제 역할 파악 | https://www.airbridge.io/blog/ko-what-is-marketing-attribution-model |
| 채널별 기여 전환 수 및 기여 매출 산출 | 각 채널이 최종 전환에 기여한 전환 수·매출 금액 정량화 | https://www.thedigitalmkt.com/marketing-attribution-guide/ |
| 전환 경로 분석 (Path Analysis) | GA4 전환 경로 보고서로 주요 전환 여정 패턴 파악, 예산 재배분 근거 도출 | https://gist.github.com/shane-shim/ae0f55a1420f0208845f83ecc103dfb7 |
| 어트리뷰션 결과 기반 예산 재배분 제안 | 분석 결과를 바탕으로 채널별 광고 예산 최적화 로드맵 제시 | https://www.singular.net/ |

---

## 19. 퍼널(Funnel) 분석 및 이탈 원인 진단

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| GA4 퍼널 탐색 보고서 설계 | GA4 탐색 분석 내 퍼널 시각화 설정, 단계별 전환율·이탈 수 측정 | https://osoma.kr/ga-consulting/ |
| 결제 퍼널 단계별 이탈 분석 | 상품 조회 → 장바구니 → 결제 시작 → 구매 완료 각 단계 이탈률 정량화 | https://www.beusable.net/blog/?p=3226 |
| 세그먼트별 퍼널 비교 분석 | 신규/재방문, 채널별, 디바이스별 퍼널 전환율 비교, 이탈 원인 세분화 | https://docs-kr.hackle.io/docs/funnel-analysis |
| 이탈 페이지 진단 및 UX 개선 제안 | 퍼널 이탈 집중 페이지 파악 후 히트맵·세션 레코딩 연계 UX 개선 제안 | https://osoma.kr/ga-consulting/ |
| 퍼널 개선 효과 측정 (Before/After) | UX 개선 후 단계별 전환율 변화 측정, 개선 효과 수치화 | https://www.beusable.net/blog/?p=3226 |

---

## 20. 사용자 행동 분석 (히트맵·세션 레코딩)

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| MS Clarity 설치 및 기본 설정 | Microsoft Clarity 무료 툴 설치, 히트맵·세션 레코딩 데이터 수집 시작 | https://brunch.co.kr/@kayros/243 |
| 클릭맵·스크롤맵 분석 | 페이지별 클릭 집중 구간·스크롤 깊이 시각화로 CTA 위치 최적화 인사이트 도출 | https://openads.co.kr/content/contentDetail?contsId=18342 |
| 세션 레코딩(Session Recording) 분석 | 실제 사용자 행동 영상 분석, 장애 요소·혼란 구간 파악 | https://blog.ab180.co/posts/amplitude-heatmap-session-replay-guide |
| 분노 클릭·사망 클릭 패턴 분석 | 클릭해도 반응 없는 요소 클릭·브라우저 강제 종료 패턴 파악 | https://brunch.co.kr/@kayros/243 |
| Hotjar / Amplitude 고급 세그먼트 분석 | 특정 전환 사용자 vs 이탈 사용자 행동 비교, 차이점 인사이트 도출 | https://amplitude.com/ko-kr/heatmaps |
| UX 개선 제안 보고서 작성 | 히트맵·세션 레코딩 분석 결과를 개선 우선순위 및 액션 아이템으로 정리 | https://brunch.co.kr/@beusable/25 |

---

## 21. A/B 테스트 설계 및 분석

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| A/B 테스트 가설 수립 및 실험 설계 | 전환율 개선 가설 정의, 대조군/실험군 분리 기준 및 성공 지표 설정 | https://www.datamarketing.co.kr/ |
| 랜딩페이지 CTA·헤드라인 A/B 테스트 | 버튼 문구·색상·위치·헤드라인 변형 테스트, 전환율 비교 | https://amplitude.com/ko-kr/web-experimentation |
| Google Optimize 대체 툴 세팅 (VWO / Optimizely / Hackle) | Google Optimize 종료 이후 대안 A/B 테스트 플랫폼 세팅 및 운영 | https://docs-kr.hackle.io/docs/funnel-analysis |
| 통계적 유의성 검증 및 결과 해석 | 샘플 사이즈 계산, p-value 기반 유의성 판단, 결과 해석 보고 | https://www.datamarketing.co.kr/ |
| 개인화 실험(Personalization Test) 설계 | 세그먼트별 맞춤 콘텐츠·오퍼 노출 실험 설계 및 성과 비교 | https://amplitude.com/ko-kr/web-experimentation |

---

## 22. CDP(고객 데이터 플랫폼) 구축 및 운영

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| CDP 솔루션 선정 컨설팅 (Airbridge / mParticle / Braze) | 비즈니스 규모·예산·기술 스택 기반 최적 CDP 솔루션 비교 선정 | https://openads.co.kr/content/contentDetail?contsId=16556 |
| 퍼스트파티 데이터 수집 체계 구축 | 웹·앱·오프라인 접점에서 퍼스트파티 데이터 수집 파이프라인 구성 | https://blog.dighty.com/business/?bmode=view&idx=12504691 |
| 통합 고객 프로필(Single Customer View) 구성 | 다채널 행동 데이터를 단일 고객 ID로 통합, 360도 고객 뷰 구축 | https://www.oracle.com/cx/customer-data-platform/what-is-cdp/ |
| 고객 세그먼트 설계 및 활성화 | 행동·구매·인구통계 기반 세그먼트 정의, 광고·이메일·앱 푸시 채널 연동 | https://www.salesforce.com/kr/hub/crm/what-is-a-cdp/ |
| CDP 데이터 품질 관리 및 업데이트 정책 수립 | 데이터 갱신 주기·중복 제거·개인정보 처리 정책 수립 | https://www.2e.co.kr/news/articleView.html?idxno=207180 |

---

## 23. CRM 데이터 분석 및 세그먼트 설계

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 구매 이력 기반 고객 등급 분류 | RFM(최근성·빈도·금액) 분석으로 VIP·이탈 위험·잠재 고객 세그먼트 구분 | https://www.itdaa.net/open_mentorings/654 |
| LTV(고객 생애 가치) 계산 모델 구성 | 평균 구매 주기·금액 기반 예상 LTV 계산, 고가치 고객군 파악 | https://www.itdaa.net/open_mentorings/654 |
| 이탈 고객 재활성화 세그먼트 설계 | 일정 기간 미구매 고객 추출, 재구매 유도 캠페인 타겟 세그먼트 생성 | https://www.salesforce.com/kr/hub/crm/what-is-a-cdp/ |
| 구매 패턴 분석 및 교차 판매 기회 발굴 | 함께 구매되는 상품 조합 분석, 업셀링·크로스셀링 캠페인 기획 근거 도출 | https://www.itdaa.net/open_mentorings/654 |
| CRM 데이터 ↔ 광고 플랫폼 맞춤타겟 연동 | CRM 고객 리스트를 Google Ads·Meta 맞춤타겟으로 업로드, 광고 정밀 타겟팅 | https://www.salesforce.com/kr/hub/crm/what-is-a-cdp/ |

---

## 24. 앱 트래킹 세팅 (AppsFlyer · Adjust · Airbridge)

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| MMP(모바일 측정 파트너) 솔루션 선정 컨설팅 | AppsFlyer·Adjust·Airbridge 기능·가격 비교, 서비스 규모별 최적 솔루션 선정 | https://www.airbridge.io/en/blog/appsflyer-vs-airbridge-vs-adjust-vs-branch-best-mmp-for-subscription-app-in-2026 |
| SDK 연동 (Android / iOS) | 앱 코드에 MMP SDK 삽입, 설치·실행·인앱 이벤트 수집 환경 구성 | https://docs.adjust.com/ko/network-integration/ |
| 앱 설치 어트리뷰션 설정 | 광고 클릭 → 앱 설치 연결, 채널별 설치 기여도 측정 | https://brunch.co.kr/@haegun/24 |
| 인앱 이벤트(In-App Event) 정의 및 등록 | 구매·레벨업·튜토리얼 완료 등 핵심 인앱 이벤트 설계 및 SDK 이벤트 매핑 | https://www.adjust.com/ko/product-comparison/adjust-vs-appsflyer/ |
| 광고 네트워크(Network) 연동 | Google Ads·Meta·카카오 광고 네트워크와 MMP 연동, 캠페인별 성과 통합 | https://support.appsflyer.com/hc/en-us/articles/360020834237 |
| 딥링크(Deep Link) 설정 | 광고 클릭 시 앱 내 특정 화면으로 이동하는 딥링크 구성, 전환율 개선 | https://www.airbridge.io/blog/best-app-marketing-measurement-tool-in-2026-for-startups-why-airbridge-core-plan-works-for-early-growth |

---

## 25. 서버사이드 태깅(Server-Side GTM) 구축

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| GCP(Google Cloud Platform) 서버 컨테이너 환경 구성 | Google Cloud Run 기반 Server-Side GTM 서버 컨테이너 배포 | https://nerdboard.kr/blog/conversion-api-event-hacking |
| 클라이언트(Client) 설정 | GA4·Universal Analytics 클라이언트 구성, 브라우저 → 서버 이벤트 라우팅 | https://nerdboard.kr/blog/conversion-api-event-hacking |
| 서버사이드 GA4 태그 구성 | 서버 컨테이너에서 GA4로 이벤트 전달하는 서버사이드 태그 생성 | https://nerdboard.kr/blog/conversion-api-event-hacking |
| 서버사이드 Meta CAPI 태그 구성 | 서버 컨테이너에서 Meta CAPI로 전환 데이터 전달, 쿠키리스 전환 추적 강화 | https://nerdboard.kr/blog/conversion-api-event-hacking |
| 퍼스트파티 쿠키(First-Party Cookie) 수명 연장 설정 | 서버사이드 환경에서 퍼스트파티 쿠키 7일→400일 수명 연장, ITP 대응 | https://nerdboard.kr/blog/conversion-api-event-hacking |

---

## 26. BigQuery 연동 및 원시 데이터 추출 환경 구축

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| GA4 ↔ BigQuery 연동 설정 | GA4 관리 화면에서 BigQuery 프로젝트 연결, 일별 이벤트 원시 데이터 자동 내보내기 | https://osoma.kr/blog/ga4-bigquery-connect/ |
| BigQuery 원시 데이터 스키마 이해 및 쿼리 설계 | GA4 BigQuery Export 스키마 구조 파악, 세션·이벤트·사용자 단위 SQL 쿼리 작성 | https://osoma.kr/blog/ga4-bigquery-sessions-users/ |
| Looker Studio ↔ BigQuery 연동 대시보드 구성 | BigQuery 쿼리 결과를 Looker Studio에 연결, 샘플링 없는 정확한 데이터 시각화 | https://hurdlers.kr/resource/case-studies/how-to-set-up-real-time-reports-ga4-bigquery |
| 장기 데이터 보관 및 비용 최적화 설정 | BigQuery 스토리지 클래스·파티셔닝 설정으로 데이터 보관 비용 최소화 | https://blog.bizspring.co.kr/테크/google-analytics-4-데이터-수집-리포트-생성/ |
| 맞춤 SQL 보고서 제작 | 표준 GA4 보고서에서 불가능한 세부 분석을 BigQuery SQL로 구현 | https://goldenplanet.co.kr/our_contents/blog?number=1013 |

---

## 27. 광고 성과 분석 리포트 (퍼포먼스 분석)

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 채널별 ROAS·CPA·CTR·CVR 집계 분석 | 채널 단위 핵심 퍼포먼스 지표 집계, 채널 효율 순위 비교 | https://home.ampm.co.kr/ae-kimyongmin/insight/9624 |
| 캠페인·광고 그룹·소재 단위 세부 분석 | 광고 계층 구조별 성과 드릴다운, 고성과·저성과 소재 파악 | https://bizspring.co.kr/company/prd_air.php |
| 기간 대비(WoW / MoM / YoY) 성과 비교 | 주간·월간·연간 성과 변화율 분석, 트렌드 및 이상 지표 파악 | https://brunch.co.kr/@project-tom/84 |
| 마진 기반 실질 ROAS 계산 | 매출이 아닌 마진 기준 ROAS 산출, 수익성 관점 광고 효율 평가 | https://fastercapital.com/ko/content/광고-투자수익--ROAS--ROAS-대-CPA--광고-캠페인의-효과를-평가하는-방법.html |
| 예산 재배분 제안 보고서 | 성과 분석 결과 기반 채널·캠페인별 예산 조정 시나리오 제안 | https://brunch.co.kr/@project-tom/84 |
| 경쟁사 광고 벤치마크 비교 | 업종 평균 CTR·CPA 대비 자사 성과 수준 비교, 개선 목표 설정 | https://home.ampm.co.kr/ae-kimyongmin/insight/9624 |

---

## 28. 데이터 분석 컨설팅 (전략·세팅 방향 수립)

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| 현행 트래킹 환경 진단(Data Audit) | 기존 GA4·픽셀·GTM 세팅 전수 점검, 누락·오류·중복 현황 파악 | https://entrench-consulting.com/ko/analytics-consulting/ |
| 측정 계획서(Measurement Plan) 수립 | 비즈니스 목표 → KPI → 이벤트·파라미터 설계까지 문서화, 개발팀 협업 기준 정의 | https://www.mfitlab.com/solutions/blog/2023-05-31-productdataanalysis-beginner-trackingplan |
| 분석 툴 스택 선정 컨설팅 | GA4·Amplitude·Mixpanel 등 분석 목적·예산 기반 최적 툴 조합 제안 | https://entrench-consulting.com/ko/analytics-consulting/ |
| 데이터 분석 우선순위 로드맵 제시 | 단기·중기·장기 트래킹 개선 과제 도출, 우선순위 매트릭스 구성 | https://occamdata.kr/ga4-setup/ |
| 내부 분석 역량 교육(내재화) | GA4 활용법·데이터 읽는 법 교육, 클라이언트 팀이 직접 분석 가능하도록 훈련 | https://osoma.kr/ga-consulting/ |

---

## 29. 마케팅 자동화 연동 데이터 세팅 (CRM + MA)

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| HubSpot·Mailchimp GA4 UTM 파라미터 연동 | MA 툴 발송 이메일에 UTM 파라미터 자동 추가, GA4 유입 채널 데이터 정확도 향상 | https://www.ab180.co/ |
| CRM 리드 데이터 ↔ GA4 이벤트 연동 | 오프라인 전환·CRM 리드 완료 이벤트를 GA4·Google Ads로 전송 | https://www.ab180.co/ |
| 자동화 트리거 이벤트 설계 | 특정 행동(장바구니 이탈, 특정 페이지 방문 등) 발생 시 CRM 자동화 워크플로우 연동 | https://www.ab180.co/ |
| 이메일·앱 푸시 오픈·클릭 데이터 GA4 연동 | MA 발송 이메일 오픈·클릭 이벤트를 GA4로 수집, 전체 고객 여정 통합 분석 | https://www.ab180.co/ |
| 자동화 캠페인 성과 추적 대시보드 구성 | MA 채널별 리드 생성·전환 성과를 통합 대시보드에서 모니터링 | https://www.ab180.co/ |

---

## 30. 데이터 품질 감사(Data Audit) 및 오류 수정

| 소분류명 | 한 줄 정의 | 출처 URL |
|---------|-----------|---------|
| GA4 이벤트 중복 수집 진단 및 제거 | gtag·GTM 이중 삽입 등 원인으로 발생하는 이벤트 중복 집계 탐지 및 수정 | https://theanalytics.co.kr/ga4-전자상거래-데이터-누락-또는-잘못된-경우-수정하기/ |
| 전환 이벤트 누락·오발동 수정 | 특정 조건에서 전환 미수집 또는 오발동되는 원인 분석 후 태그 수정 | https://openads.co.kr/content/contentDetail?contsId=11587 |
| 데이터 품질 지표(Data Quality Indicator) 점검 | GA4 관리 화면 데이터 품질 지표 확인, 경고 항목 분석 및 개선 | https://support.google.com/analytics/answer/13800978?hl=ko |
| 직접 유입(Direct) 과다 집계 원인 분석 및 수정 | UTM 누락·리다이렉트 문제로 직접 유입 집계 비율 비정상적으로 높은 경우 원인 파악 | https://entrench-consulting.com/ko/ga4-google-analytics-4/ |
| 픽셀·GTM 태그 충돌 진단 | 복수 픽셀 삽입·태그 실행 순서 충돌로 인한 데이터 오염 진단 및 정리 | https://entrench-consulting.com/ko/ga4-google-analytics-4/ |
| 감사 결과 보고서 및 정비 로드맵 제공 | 전수 점검 결과 문서화, 수정 우선순위 및 예상 소요 일정 포함 정비 계획서 제공 | https://entrench-consulting.com/ko/ga4-google-analytics-4/ |

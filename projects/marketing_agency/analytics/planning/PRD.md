# PRD — 데이터 분석 / 트래킹 서비스 시스템

> Product Requirement Document — 개발팀 인계용 문서

---

## 0. 개요

마케팅 에이전시의 데이터 분석/트래킹 서비스를 지원하는 백엔드 + 프론트엔드 시스템. 클라이언트별 GA4, 픽셀, 광고 데이터를 수집/통합/시각화하고, 월별 성과 리포트를 자동 생성한다.

**핵심 기능:**
1. 클라이언트별 데이터 통합 수집 (GA4, Meta, Google Ads, Naver 등)
2. 실시간 커스텀 대시보드 (Looker Studio와 유사, 또는 커스텀 개발)
3. 월별 성과 리포트 자동 생성 (PDF)
4. 트래킹 데이터 품질 모니터링
5. 이벤트 검증 도구 (개발팀용)

---

## 1. 시스템 개요

### 1-1. 핵심 가치

| 가치 | 설명 |
|------|------|
| **자동화** | 월별 리포트 80% 이상 자동 생성 (수동 시간 2시간 → 20분) |
| **데이터 통합** | 광고 채널 5곳 이상 데이터를 한 곳에서 추적 (3개 도구 접근 시간 60% 감소) |
| **실시간 모니터링** | 대시보드를 통해 실시간 성과 조회 가능 (일일 미팅 자동 불필요) |
| **품질 보증** | 트래킹 데이터 이상 자동 감지 → Slack 알림 (수동 감시 불필요) |

### 1-2. 비즈니스 목표

**6개월 목표:**
- 100+ 클라이언트 온보딩 지원 (월 [x]명)
- 월별 리포트 자동화율 80%+ 달성
- 클라이언트 만족도 (NPS) 50+ 달성
- 데이터 추적 정확도 > 95% 유지

---

## 2. 시스템 아키텍처

### 2-1. 전체 구조

```
┌─────────────────────────────────────────────┐
│     클라이언트 / 외부 API                      │
│ (GA4, Meta, Google Ads, Naver, Kakao)      │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ↓                     ↓
┌──────────────────┐  ┌──────────────────┐
│   데이터 수집     │  │   검증 엔진       │
│   (Batch Job)   │  │  (Data Quality)  │
│                  │  │                  │
│ • GA4 API        │  │ • 이상 감지       │
│ • Meta API       │  │ • 데이터 검증     │
│ • Google API     │  │ • Slack 알림     │
│ • Naver API      │  │                  │
│ • Kakao API      │  │                  │
└──────────────────┘  └──────────────────┘
        │                    │
        └──────────┬─────────┘
                   ↓
        ┌──────────────────────┐
        │   데이터 저장소       │
        │ (PostgreSQL/TimescaleDB)
        │                      │
        │ • clients 테이블     │
        │ • daily_metrics     │
        │ • events            │
        │ • campaigns         │
        └──────────┬───────────┘
                   │
        ┌──────────┴──────────┐
        ↓                     ↓
┌──────────────────┐  ┌──────────────────┐
│  리포트 생성      │  │  대시보드 API     │
│  (Report Engine) │  │  (Backend API)   │
│                  │  │                  │
│ • PDF 생성       │  │ • RESTful API    │
│ • 이메일 발송    │  │ • GraphQL        │
│ • 클라우드 저장  │  │ • WebSocket      │
└──────────────────┘  └──────────────────┘
                              │
                              ↓
                    ┌──────────────────────┐
                    │  프론트엔드           │
                    │ (React/Vue.js)       │
                    │                      │
                    │ • 대시보드            │
                    │ • 리포트 뷰          │
                    │ • 이벤트 검증 도구   │
                    │ • CRM                │
                    └──────────────────────┘
```

### 2-2. 데이터 흐름

```
Day 1-5: 기본 설정
├─ GA4/GTM 설정
├─ 픽셀 설치
└─ 데이터 수집 시작

Day 5+: 정상 운영
├─ 매일 00:00 (자정)
│  └─ 전날 데이터 수집
│     ├─ GA4 API → 이벤트/세션 데이터
│     ├─ Meta API → 지출/클릭/전환
│     ├─ Google Ads API → 지출/CPA/ROAS
│     ├─ Naver API → 지출/전환
│     └─ Kakao API → 지출/전환
│
├─ 데이터 저장
│  └─ daily_metrics 테이블에 저장
│
├─ 검증 엔진 실행
│  ├─ 데이터 이상 감지 (전일 대비 ±50% 이상)
│  ├─ 수집 실패 확인
│  └─ 이상 감지 시 Slack 알림
│
├─ 실시간 대시보드 업데이트
│  └─ Looker Studio 또는 커스텀 대시보드 갱신
│
└─ 월말 23:55
   └─ 월별 리포트 생성 및 이메일 발송
      ├─ Python/Node.js로 PDF 생성
      ├─ 클라우드(Google Drive/S3)에 저장
      └─ 클라이언트에게 이메일 발송
```

---

## 3. 핵심 기능 상세

### 기능 1: 데이터 통합 수집

**목적:** GA4, Meta, Google Ads, Naver, Kakao 등 다양한 데이터 소스에서 자동으로 데이터를 수집

**사용 기술:**
- Python Batch Job (Celery/Airflow) 또는 AWS Lambda
- 각 플랫폼 공식 API (OAuth 2.0 인증)
- Webhook (선택사항, 실시간 업데이트 필요 시)

**구현 상세:**

**3-1-1. GA4 API 연동**
- Endpoint: `https://analyticsreporting.googleapis.com/v4/reports:batchGet`
- 수집 데이터:
  ```
  - 일별 활성 사용자(users)
  - 세션(sessions)
  - 이벤트(events) — 커스텀 이벤트 포함
  - 전환(conversions)
  - 사용자 행동(event_name, event_parameters)
  ```
- 주기: 매일 자정 (UTC+9)
- 코드 예시 (Python):
  ```python
  from google.analytics.data_v1beta import BetaAnalyticsDataClient
  from google.analytics.data_v1beta.types import (
      RunReportRequest, DateRange, Dimension, Metric
  )
  
  def fetch_ga4_data(property_id: str, start_date: str, end_date: str):
      client = BetaAnalyticsDataClient()
      request = RunReportRequest(
          property=f"properties/{property_id}",
          date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
          dimensions=[Dimension(name="date"), Dimension(name="eventName")],
          metrics=[Metric(name="eventCount")],
      )
      response = client.run_report(request)
      return response
  ```

**3-1-2. Meta Conversions API (CAPI) 수집**
- Endpoint: `https://graph.instagram.com/v18.0/{ad_account_id}/insights`
- 수집 데이터:
  ```
  - 지출액(spend)
  - 클릭(clicks)
  - 노출(impressions)
  - 전환(conversions)
  - 클릭당비용(cpc)
  - 전환당비용(cpa)
  - ROAS(return_on_ad_spend)
  ```
- 주기: 매일 자정, 실시간 업데이트 (Webhook)
- 코드 예시:
  ```python
  import requests
  
  def fetch_meta_ads_data(ad_account_id: str, access_token: str):
      url = f"https://graph.instagram.com/v18.0/{ad_account_id}/insights"
      params = {
          "access_token": access_token,
          "date_preset": "yesterday",
          "fields": "spend,clicks,impressions,actions,action_values"
      }
      response = requests.get(url, params=params)
      return response.json()
  ```

**3-1-3. Google Ads API 수집**
- SDK: `google-ads` (Python)
- 수집 데이터:
  ```
  - 캠페인/광고그룹 성과
  - 지출, 클릭, 노출, 전환
  - CTR, CPC, CPA, ROAS
  ```
- 코드 예시:
  ```python
  from google.ads.googleads.client import GoogleAdsClient
  
  def fetch_google_ads_data(customer_id: str, credentials_path: str):
      client = GoogleAdsClient.load_from_storage(credentials_path)
      query = """
          SELECT campaign.name, campaign.id, metrics.cost_micros, 
                 metrics.conversions, metrics.clicks
          FROM campaign
          WHERE segments.date BETWEEN '2026-04-14' AND '2026-04-15'
      """
      ga_service = client.get_service("GoogleAdsService")
      results = ga_service.search_stream(customer_id, query)
      return results
  ```

**3-1-4. Naver Ads API 수집**
- Endpoint: Naver Ads API v2
- 수집 데이터:
  ```
  - 캠페인별 지출, 클릭, 전환
  - 일별/시간별 성과
  ```

**3-1-5. Kakao Ads API 수집**
- Endpoint: Kakao Ads API
- 수집 데이터:
  ```
  - 광고 성과 (지출, 클릭, 전환)
  - 플랫폼: 카카오 톡, 카카오 스토리 등
  ```

**데이터 저장 (PostgreSQL/TimescaleDB):**
```sql
-- daily_metrics 테이블 (시계열 데이터 최적화)
CREATE TABLE daily_metrics (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id),
    date DATE NOT NULL,
    platform VARCHAR(50), -- 'GA4', 'META', 'GOOGLE_ADS', 'NAVER', 'KAKAO'
    
    -- 기본 지표
    spend DECIMAL(12,2),
    clicks INTEGER,
    impressions INTEGER,
    conversions INTEGER,
    
    -- 계산 지표
    cpc DECIMAL(10,4),
    cpa DECIMAL(10,2),
    roas DECIMAL(10,4),
    ctr DECIMAL(10,4),
    conversion_rate DECIMAL(10,4),
    
    -- 메타데이터
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    data_quality_score DECIMAL(5,2) -- 데이터 품질 (0-100)
);

CREATE INDEX idx_daily_metrics_client_date ON daily_metrics(client_id, date);
CREATE INDEX idx_daily_metrics_platform ON daily_metrics(platform);
```

---

### 기능 2: 실시간 대시보드

**목적:** 클라이언트가 광고 성과를 실시간으로 조회 가능한 대시보드 제공

**구현 방안:**
- **Option 1 (권장):** Looker Studio (Google 공식 도구, 무료)
  - 장점: GA4 네이티브 연동, 빠른 개발, 유지보수 최소
  - 단점: 커스터마이징 제한
- **Option 2:** 커스텀 대시보드 (React + Chart.js/D3.js)
  - 장점: 완전한 커스터마이징 가능
  - 단점: 개발 시간 길음, 유지보수 필요

**권장: Looker Studio 기본 + 커스텀 대시보드 보완**

**대시보드 화면 구성:**

**대시보드 1: Executive Summary**
```
┌────────────────────────────────────┐
│ 2026년 4월 성과 요약                 │
├────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│ │ 지출     │ │ ROAS    │ │ CPA     ││
│ │ 1,500만 │ │ 3.2배  │ │ 6,000원 ││
│ └─────────┘ └─────────┘ └─────────┘│
├────────────────────────────────────┤
│ 채널별 지출 비율                      │
│ 메타 ████████░░ 50% (750만원)       │
│ 구글 ████░░░░░░ 30% (450만원)       │
│ 네이버 ██░░░░░░░░ 20% (300만원)      │
├────────────────────────────────────┤
│ 지난 30일 추이                       │
│ [그래프: 일일 ROAS 변화]              │
└────────────────────────────────────┘
```

**대시보드 2: 채널 성과**
```
┌────────────────────────────────────┐
│ 채널별 상세 분석                     │
├────────────────────────────────────┤
│ 메타 광고                            │
│ 지출: 750만 | 클릭: 3,000 | 전환: 100
│ CPA: 7,500원 | ROAS: 3.5배         │
│                                     │
│ 구글 애즈                            │
│ 지출: 450만 | 클릭: 2,000 | 전환: 80
│ CPA: 5,625원 | ROAS: 3.0배         │
│                                     │
│ 네이버 광고                          │
│ 지출: 300만 | 클릭: 1,500 | 전환: 50
│ CPA: 6,000원 | ROAS: 2.5배         │
└────────────────────────────────────┘
```

**대시보드 3: 일일 모니터링 (실시간)**
```
┌────────────────────────────────────┐
│ 오늘 성과 (업데이트: 23:45)           │
├────────────────────────────────────┤
│ 지출: 5만원                         │
│ 클릭: 200                           │
│ 전환: 8                             │
│ CPA: 6,250원                        │
│                                     │
│ 시간대별 성과                        │
│ [그래프: 시간별 클릭/전환 변화]       │
└────────────────────────────────────┘
```

---

### 기능 3: 월별 성과 리포트 자동 생성

**목적:** 매월 자동으로 성과 리포트 생성 및 이메일 발송

**기술 스택:**
- Python Docx (Word 문서 생성) 또는 Jinja2 + wkhtmltopdf (HTML → PDF)
- Celery (스케줄러)
- SendGrid 또는 AWS SES (이메일)
- Google Drive 또는 AWS S3 (클라우드 저장)

**실행 프로세스:**
```
월별 리포트 생성 (매월 1일 23:00 KST)
├─ 전월 데이터 추출
│  ├─ daily_metrics에서 지난달 데이터 조회
│  ├─ GA4에서 이벤트 데이터 추출
│  └─ 광고 채널별 성과 데이터 수집
│
├─ 리포트 계산
│  ├─ KPI 계산 (ROAS, CPA, CTR 등)
│  ├─ 채널별 비교 분석
│  ├─ 크리에이티브 성과 TOP 3
│  └─ 이상 데이터 진단
│
├─ 리포트 템플릿 렌더링
│  ├─ Jinja2 템플릿에 데이터 주입
│  └─ 차트/이미지 생성 (matplotlib)
│
├─ PDF 생성
│  ├─ HTML → PDF 변환 (wkhtmltopdf)
│  └─ 최종 PDF 파일 생성
│
├─ 클라우드 저장
│  ├─ Google Drive에 업로드
│  └─ 공유 링크 생성
│
└─ 이메일 발송
   ├─ SendGrid API 호출
   ├─ 리포트 PDF 첨부
   ├─ 클라이언트 메일링 리스트에 발송
   └─ 로그 기록
```

**리포트 구성 (자동 생성 항목):**

1. **Executive Summary** (자동)
   ```
   - 월 지출액
   - 월 전환 건수
   - 월 ROAS
   - 월 CPA
   - 목표 대비 달성율 (백분율)
   ```

2. **KPI 대시보드** (자동)
   ```
   - 카드형 KPI: 지출, CPA, ROAS, 전환율
   - 색상 코딩 (초록: 목표달성, 주황: 경계, 빨강: 미달)
   ```

3. **채널별 분석** (자동)
   ```
   - 메타: 지출, 클릭, 전환, CPA, ROAS
   - 구글: 지출, 클릭, 전환, CPA, ROAS
   - 네이버: 지출, 클릭, 전환, CPA, ROAS
   - 카카오: (있을 경우)
   
   - 채널별 비교 차트
   - 채널 성과 평가 (우수/정상/개선필요)
   ```

4. **트래킹 데이터 품질** (자동)
   ```
   - 데이터 수집율 (%)
   - 이벤트별 발생 건수
   - 발견된 이상 데이터
   - 개선 권고사항
   ```

5. **최적화 제안** (반자동 + 수동 추가)
   ```
   - 분석: 이전 달 대비 성과 변화 (자동)
   - 제안: AI 기반 최적화 아이디어 (자동 또는 수동)
   - 액션: 다음 달 실행 항목 (수동, PM이 추가)
   ```

**코드 예시 (Python):**
```python
from jinja2 import Template
from weasyprint import HTML
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText

def generate_monthly_report(client_id: str, year: int, month: int):
    # 1. 데이터 추출
    previous_month_data = fetch_monthly_data(client_id, year, month-1)
    
    # 2. 계산
    kpi = calculate_kpi(previous_month_data)
    
    # 3. 템플릿 렌더링
    template_path = 'templates/monthly_report.html'
    with open(template_path, 'r') as f:
        template = Template(f.read())
    
    html_content = template.render(
        client_name=get_client_name(client_id),
        year=year,
        month=month,
        kpi=kpi,
        channels=previous_month_data,
        recommendations=get_ai_recommendations(client_id, previous_month_data)
    )
    
    # 4. PDF 생성
    pdf_path = f'/reports/{client_id}_{year}_{month}.pdf'
    HTML(string=html_content).write_pdf(pdf_path)
    
    # 5. 클라우드 저장
    google_drive_url = upload_to_google_drive(pdf_path)
    
    # 6. 이메일 발송
    send_report_email(client_id, pdf_path, google_drive_url)
    
    return google_drive_url
```

---

### 기능 4: 데이터 품질 모니터링

**목적:** 트래킹 데이터 이상을 자동 감지하고 즉시 알림

**모니터링 항목:**

| 항목 | 기준 | 동작 |
|------|------|------|
| **데이터 수집 중단** | 24시간 이상 데이터 없음 | Slack 긴급 알림 |
| **비정상적 증감** | 전일 대비 ±50% 이상 | Slack 경고 |
| **이벤트 누락** | 정의된 이벤트 발생 0건 | 일일 리포트 기록 |
| **파라미터 오류** | 파라미터 누락율 > 10% | 주간 리포트 |
| **중복 데이터** | 중복 이벤트 감지 | 데이터 정제 + 로그 |

**구현:**
```python
def monitor_data_quality(client_id: str):
    today_data = fetch_daily_metrics(client_id, date.today())
    yesterday_data = fetch_daily_metrics(client_id, date.today() - timedelta(days=1))
    
    # 1. 데이터 수집 확인
    if not today_data or today_data['events'] == 0:
        send_slack_alert(f"⚠️ {client_id} 데이터 수집 중단")
    
    # 2. 비정상 증감 확인
    growth_rate = (today_data['spend'] - yesterday_data['spend']) / yesterday_data['spend']
    if growth_rate > 0.5 or growth_rate < -0.5:
        send_slack_alert(f"⚠️ {client_id} 지출 {growth_rate*100:.1f}% 변화")
    
    # 3. 이벤트 누락 확인
    for event_name in get_tracked_events(client_id):
        if today_data[event_name] == 0:
            log_quality_issue(client_id, event_name, "event_missing")
    
    return quality_score
```

---

### 기능 5: 이벤트 검증 도구

**목적:** 개발자가 GA4 이벤트 설정을 검증할 수 있는 도구 제공

**기능:**
- GA4 Debug View 데이터 실시간 표시
- 설정된 커스텀 이벤트 목록 표시
- 이벤트 발생 시뮬레이션 (테스트 버튼)
- 파라미터 값 검증 (타입, 범위 확인)

**UI/UX:**
```
이벤트 검증 도구 (GA4 Debug View)
┌──────────────────────────────────┐
│ [클라이언트 선택 ▼] [새로고침]     │
├──────────────────────────────────┤
│ 추적 중인 이벤트:                  │
│ □ button_click (발생: 0/시간)      │
│ □ form_submit (발생: 0/시간)       │
│ □ product_view (발생: 123/시간)    │
│ □ purchase (발생: 5/시간) ✓ 정상   │
├──────────────────────────────────┤
│ 최근 이벤트 로그:                  │
│ 14:35:22 | purchase               │
│           product_id: "SKU-001"   │
│           value: 29900            │
│           currency: "KRW"         │
│                                   │
│ 14:32:15 | button_click           │
│           button_id: "submit-btn" │
└──────────────────────────────────┘
```

---

## 4. API 명세

### 4-1. Backend API (RESTful)

**Base URL:** `https://api.analytics-service.com/v1`

#### Endpoint 1: 클라이언트 목록 조회
```
GET /clients
Query Parameters:
  - limit: 20 (기본값)
  - offset: 0 (기본값)
  - status: 'active' | 'inactive' (선택)

Response:
{
  "data": [
    {
      "id": "client-123",
      "name": "홍길동 쇼핑몰",
      "status": "active",
      "created_at": "2026-04-15T00:00:00Z",
      "services": ["ga4", "meta_pixel", "looker_studio"],
      "next_report_date": "2026-05-01"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

#### Endpoint 2: 일일 성과 데이터 조회
```
GET /clients/{client_id}/metrics
Query Parameters:
  - date_from: "2026-04-01" (YYYY-MM-DD)
  - date_to: "2026-04-15"
  - platform: 'all' | 'GA4' | 'META' | 'GOOGLE_ADS' | 'NAVER' (선택)

Response:
{
  "data": [
    {
      "date": "2026-04-15",
      "platform": "META",
      "spend": 750000,
      "clicks": 3000,
      "impressions": 50000,
      "conversions": 100,
      "cpc": 250,
      "cpa": 7500,
      "roas": 3.2,
      "ctr": 6.0,
      "data_quality_score": 98.5
    }
  ]
}
```

#### Endpoint 3: 월별 리포트 조회
```
GET /clients/{client_id}/reports/{year}/{month}

Response:
{
  "id": "report-202604",
  "client_id": "client-123",
  "year": 2026,
  "month": 4,
  "pdf_url": "https://drive.google.com/...",
  "generated_at": "2026-05-01T00:15:00Z",
  "metrics": {
    "total_spend": 1500000,
    "total_conversions": 250,
    "avg_roas": 3.2,
    "avg_cpa": 6000
  }
}
```

#### Endpoint 4: 이벤트 로그 조회
```
GET /clients/{client_id}/events
Query Parameters:
  - event_name: "purchase" (선택)
  - limit: 100 (기본값)

Response:
{
  "data": [
    {
      "timestamp": "2026-04-15T14:35:22Z",
      "event_name": "purchase",
      "parameters": {
        "product_id": "SKU-001",
        "value": 29900,
        "currency": "KRW"
      },
      "source": "GA4"
    }
  ]
}
```

---

## 5. 데이터베이스 스키마

### 주요 테이블

```sql
-- 클라이언트 테이블
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'paused'
    package VARCHAR(20), -- 'starter', 'standard', 'premium'
    monthly_fee DECIMAL(10,2),
    contract_start_date DATE,
    contract_end_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 일일 성과 데이터
CREATE TABLE daily_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    date DATE NOT NULL,
    platform VARCHAR(50), -- 'GA4', 'META', 'GOOGLE_ADS', 'NAVER', 'KAKAO'
    spend DECIMAL(12,2),
    clicks INTEGER,
    impressions INTEGER,
    conversions INTEGER,
    cpc DECIMAL(10,4),
    cpa DECIMAL(10,2),
    roas DECIMAL(10,4),
    ctr DECIMAL(10,4),
    data_quality_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_daily_metrics UNIQUE(client_id, date, platform)
);

-- 커스텀 이벤트 정의
CREATE TABLE custom_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    event_name VARCHAR(100) NOT NULL,
    event_description TEXT,
    parameters JSONB, -- 파라미터 스키마 정의
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'deprecated'
    created_at TIMESTAMP DEFAULT NOW()
);

-- 월별 리포트
CREATE TABLE monthly_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    pdf_url VARCHAR(500),
    generated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_monthly_report UNIQUE(client_id, year, month)
);

-- 데이터 품질 로그
CREATE TABLE data_quality_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    date DATE,
    issue_type VARCHAR(50), -- 'missing_data', 'anomaly', 'duplicate', etc.
    issue_detail TEXT,
    severity VARCHAR(20), -- 'info', 'warning', 'critical'
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 6. 기술 스택

| 레이어 | 기술 |
|--------|------|
| **백엔드** | Python (FastAPI) 또는 Node.js (Express) |
| **데이터베이스** | PostgreSQL (관계형) + TimescaleDB (시계열) |
| **작업 스케줄러** | Celery (Python) 또는 Bull (Node.js) |
| **클라우드 저장소** | Google Drive API 또는 AWS S3 |
| **이메일** | SendGrid 또는 AWS SES |
| **프론트엔드** | React.js 또는 Vue.js |
| **차트 라이브러리** | Chart.js, D3.js, Plotly |
| **PDF 생성** | wkhtmltopdf 또는 WeasyPrint (Python) |
| **인증** | JWT (Bearer Token) |
| **API 문서** | Swagger/OpenAPI |

---

## 7. 개발 우선순위

### Phase 1: MVP (8주)
- [ ] 클라이언트 관리 (CRM) 기본 기능
- [ ] GA4 API 연동 (데이터 수집)
- [ ] 일일 성과 데이터 저장
- [ ] 기본 대시보드 API
- [ ] 수동 리포트 생성 도구

### Phase 2: 자동화 (8주)
- [ ] 월별 리포트 자동 생성 (PDF)
- [ ] 이메일 자동 발송
- [ ] 데이터 품질 모니터링
- [ ] Slack 알림 통합
- [ ] Meta/Google/Naver API 추가 연동

### Phase 3: 고도화 (12주)
- [ ] 커스텀 대시보드 (Looker Studio 통합)
- [ ] 이벤트 검증 도구
- [ ] AI 기반 최적화 제안
- [ ] 클라이언트 포탈 (셀프 서비스)
- [ ] 모바일 앱 (iOS/Android)

---

## 8. 완료 기준

**개발 완료 체크리스트:**
- [ ] 모든 API 엔드포인트 구현 및 테스트
- [ ] 월별 리포트 자동 생성 기능 검증
- [ ] 데이터 품질 모니터링 알림 정상 작동
- [ ] 5개 광고 플랫폼 API 연동 완료
- [ ] 대시보드 실시간 데이터 업데이트 확인
- [ ] 99.5% 이상 시스템 가용성 확보
- [ ] 문서화 (API Docs, 운영 매뉴얼) 완료
- [ ] QA 테스트 통과율 95% 이상

---

**PRD 작성일**: 2026년 4월 15일  
**버전**: v1.0  
**최종 검토**: CTO 승인 대기

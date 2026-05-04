> **LAINCP 자동 생성 프로젝트**
> 리안 컴퍼니 파이프라인이 생성한 구현 지시서야.
> 이 폴더에서 Claude Code 열고 `/work` 입력하면 Wave 1~6 자동 실행돼.
>
> - **프로젝트 유형**: 상용화 서비스
> - **아이디어**: 소상공인 실연락처 수집 자동화 시스템 — 구글 비즈니스 프로필, 당근마켓 업체 프로필, 네이버 블로그, 인스타그램 비즈니스 계정에서 실제 영업 가능한 업체 연락처(전화번호/카카오톡/이메일)를 자동 수집. 안심번호(050) 자동 필터링, 업종별 분류, CSV 출력. 발송은 사람이 직접 함 — 수집 전용 툴. 마케팅 에이전시 내부용 먼저, 이후 SaaS 판매 예정.
> - **생성일**: 2026-03-22

---

# 소상공인 실연락처 수집 자동화 시스템 — 구현 지시서

## 기술 스택

| 항목 | 선택 | 버전 |
|------|------|------|
| 런타임 | Node.js | 20.x LTS |
| 프레임워크 (백엔드) | Express | 4.18.x |
| 프레임워크 (프론트엔드) | Next.js | 14.x (App Router) |
| 언어 | TypeScript | 5.3.x |
| DB | PostgreSQL | 16.x |
| ORM | Prisma | 5.x |
| 작업 큐 | BullMQ | 5.x |
| 큐 브로커 | Redis | 7.x |
| 스크래핑 | Playwright | 1.42.x |
| 스크래핑 보조 | Cheerio | 1.0.x |
| 인증 | NextAuth.js | 4.x (Credentials Provider) |
| CSS | Tailwind CSS | 3.4.x |
| UI 컴포넌트 | shadcn/ui | latest |
| CSV 생성 | csv-stringify | 6.x |
| 스케줄러 | BullMQ (repeat job 미사용, 수동 트리거만) | — |
| 컨테이너 | Docker + Docker Compose | — |
| 환경변수 관리 | dotenv | — |

---

## 폴더 구조

```
contact-collector/
├── apps/
│   ├── web/                          # Next.js 프론트엔드
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   └── login/
│   │   │   │       └── page.tsx
│   │   │   ├── (dashboard)/
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx                  # 작업 목록 (대시보드)
│   │   │   │   ├── jobs/
│   │   │   │   │   ├── new/
│   │   │   │   │   │   └── page.tsx          # 작업 설정
│   │   │   │   │   └── [id]/
│   │   │   │   │       ├── page.tsx          # 수집 결과 상세
│   │   │   │   │       └── error/
│   │   │   │   │           └── page.tsx      # 오류 상세
│   │   │   ├── api/
│   │   │   │   ├── auth/
│   │   │   │   │   └── [...nextauth]/
│   │   │   │   │       └── route.ts
│   │   │   │   ├── jobs/
│   │   │   │   │   ├── route.ts              # GET 목록 / POST 생성
│   │   │   │   │   └── [id]/
│   │   │   │   │       ├── route.ts          # GET 상세 / DELETE
│   │   │   │   │       ├── results/
│   │   │   │   │       │   └── route.ts      # GET 결과 목록
│   │   │   │   │       ├── download/
│   │   │   │   │       │   └── route.ts      # GET CSV 다운로드
│   │   │   │   │       └── retry/
│   │   │   │   │           └── route.ts      # POST 재시도
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── ui/                           # shadcn/ui 컴포넌트
│   │   │   ├── jobs/
│   │   │   │   ├── JobTable.tsx
│   │   │   │   ├── JobStatusBadge.tsx
│   │   │   │   ├── JobCreateForm.tsx
│   │   │   │   ├── JobResultSummary.tsx
│   │   │   │   ├── JobResultTable.tsx
│   │   │   │   └── JobErrorDetail.tsx
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       └── Sidebar.tsx
│   │   ├── lib/
│   │   │   ├── auth.ts                       # NextAuth 설정
│   │   │   ├── prisma.ts                     # Prisma 클라이언트 싱글톤
│   │   │   └── api.ts                        # fetch 유틸
│   │   ├── next.config.js
│   │   ├── tailwind.config.ts
│   │   └── package.json
│   │
│   └── worker/                       # BullMQ 워커 (별도 프로세스)
│       ├── src/
│       │   ├── index.ts                      # 워커 엔트리포인트
│       │   ├── queue.ts                      # BullMQ 큐 정의
│       │   ├── processor.ts                  # 작업 처리 오케스트레이터
│       │   ├── scrapers/
│       │   │   ├── base.scraper.ts           # 추상 베이스 클래스
│       │   │   ├── google.scraper.ts         # 구글 비즈니스 프로필
│       │   │   ├── naver.scraper.ts          # 네이버 블로그
│       │   │   ├── daangn.scraper.ts         # 당근마켓 업체
│       │   │   └── instagram.scraper.ts      # 인스타그램 비즈니스
│       │   ├── filters/
│       │   │   ├── phone.filter.ts           # 050 안심번호 필터
│       │   │   └── duplicate.filter.ts       # 중복 제거
│       │   ├── classifiers/
│       │   │   └── category.classifier.ts    # 업종 자동 분류
│       │   └── utils/
│       │       ├── phone.parser.ts           # 전화번호 정규화
│       │       └── contact.extractor.ts      # 텍스트에서 연락처 추출
│       └── package.json
│
├── packages/
│   └── shared/                       # 공유 타입 정의
│       ├── src/
│       │   └── types.ts
│       └── package.json
│
├── prisma/
│   └── schema.prisma
├── docker-compose.yml
├── .env.example
└── package.json                      # 루트 (pnpm workspace)
```

---

## 데이터 모델

```prisma
// prisma/schema.prisma

generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// 내부 사용자 (단일 조직, Phase 1)
model User {
  id           String   @id @default(cuid())
  email        String   @unique
  passwordHash String
  name         String
  createdAt    DateTime @default(now())
  jobs         Job[]
}

// 수집 작업
model Job {
  id            String     @id @default(cuid())
  name          String                          // "강남구 카페 2025-01"
  keyword       String                          // "강남구 카페"
  region        String?                         // "서울 강남구"
  limitCount    Int        @default(100)        // 수집 건수 상한
  platforms     Platform[]                      // 선택된 플랫폼 목록
  status        JobStatus  @default(PENDING)
  totalRaw      Int        @default(0)          // 전체 수집(필터 전)
  filteredCount Int        @default(0)          // 050 제거 건수
  validCount    Int        @default(0)          // 최종 유효 건수
  errorMessage  String?
  createdAt     DateTime   @default(now())
  startedAt     DateTime?
  completedAt   DateTime?
  userId        String
  user          User       @relation(fields: [userId], references: [id])
  results       Contact[]
  errors        JobError[]

  @@index([status])
  @@index([userId, createdAt(sort: Desc)])
}

enum JobStatus {
  PENDING
  RUNNING
  COMPLETED
  FAILED
}

enum Platform {
  GOOGLE
  NAVER
  DAANGN
  INSTAGRAM
}

// 수집된 연락처
model Contact {
  id          String    @id @default(cuid())
  jobId       String
  job         Job       @relation(fields: [jobId], references: [id], onDelete: Cascade)
  bizName     String                          // 업체명
  category    String?                         // 업종 (음식점, 뷰티, 인테리어 등)
  phone       String?                         // 정규화된 전화번호
  kakao       String?                         // 카카오톡 채널 URL or ID
  email       String?                         // 이메일
  sources     Platform[]                      // 수집 출처 (중복 시 여러 개)
  rawSources  String[]                        // 원본 URL 목록
  collectedAt DateTime  @default(now())

  @@index([jobId])
  @@index([phone])
  @@index([email])
}

// 작업별 오류 로그
model JobError {
  id        String   @id @default(cuid())
  jobId     String
  job       Job      @relation(fields: [jobId], references: [id], onDelete: Cascade)
  platform  Platform
  message   String
  stack     String?
  occurredAt DateTime @default(now())

  @@index([jobId])
}
```

---

## API 엔드포인트

| Method | Path | 설명 | 인증 |
|--------|------|------|------|
| POST | `/api/auth/[...nextauth]` | NextAuth 로그인/로그아웃 | — |
| GET | `/api/jobs` | 작업 목록 조회 (페이지네이션, 상태 필터) | ✅ |
| POST | `/api/jobs` | 새 작업 생성 + BullMQ 큐 등록 | ✅ |
| GET | `/api/jobs/[id]` | 작업 상세 (요약 카드 데이터) | ✅ |
| DELETE | `/api/jobs/[id]` | 작업 삭제 (결과 포함 cascade) | ✅ |
| GET | `/api/jobs/[id]/results` | 결과 목록 (페이지네이션 50건) | ✅ |
| GET | `/api/jobs/[id]/download` | CSV 파일 스트림 다운로드 | ✅ |
| POST | `/api/jobs/[id]/retry` | 실패 작업
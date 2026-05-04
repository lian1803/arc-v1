# 2차 서칭: 챗봇·AI 서비스 개발 — 중분류
조사일: 2026-04-15
대분류: 챗봇·AI 서비스 개발
조사자: 재원

---

## 중분류 리스트

---

### 1. 카카오톡 챗봇 개발 (오픈빌더 기반)

- **한 줄 정의**: 카카오 i 오픈빌더를 활용해 카카오톡 채널에 자동응답·시나리오 챗봇을 구축하는 서비스. 규칙 기반(키워드/버튼) 위주이며 LLM 연동 없이도 가능.
- **바이브코딩 가능 여부**: 중간. 오픈빌더 UI 작업이 주이나, 외부 API(웹훅) 연동 시 코딩 필요. 바이브코딩으로 웹훅 서버 빠르게 구성 가능.
- **출처 URL**:
  - https://kmong.com/prices/%EB%B4%87-%EC%B1%97%EB%B4%87
  - https://kmong.com/gig/216313
  - https://i.kakao.com/pricing
  - https://money.dbwnsl.com/entry/%EC%B9%B4%EC%B9%B4%EC%98%A4-%EC%B1%97%EB%B4%87-%EB%A7%8C%EB%93%9C%EB%8A%94%EB%B2%95-%EB%B9%84%EC%9A%A9
- **시장 단가**:
  - 최저: 15,000원 (크몽 단순 시나리오 셋업, 기존 오픈빌더 계정 있을 때)
  - 평균: 10만~30만원 (시나리오 5~15개, 카카오채널 연동 기본 세팅)
  - 에이전시: 100만~500만원+ (복잡한 분기 시나리오 + CRM 연동 + 유지보수 포함)
- **결제 구조**: 1회 개발비 선불 + 운영비(월정액) 옵션. 카카오 오픈빌더 자체는 월 활성채팅방 5만건 무료, 초과 시 건당 30원(지식+ 40원).
- **업계 명칭 변형**: 카톡 봇, 플러스친구 챗봇, 카카오 자동응답, 카카오채널 봇

---

### 2. 텔레그램 / 디스코드 봇 개발

- **한 줄 정의**: Python(python-telegram-bot, discord.py) 등으로 텔레그램 또는 디스코드 서버에 명령어·자동화·알림 봇을 구축하는 서비스. 커뮤니티·NFT·코인 커뮤니티 수요가 높음.
- **바이브코딩 가능 여부**: 높음. API 문서가 잘 정비돼 있어 Cursor/Claude Code로 빠른 구현 가능. 보일러플레이트 코드 비중이 높아 바이브코딩 적합.
- **출처 URL**:
  - https://kmong.com/gig/122005
  - https://kmong.com/gig/357865
  - https://kmong.com/gig/573718
  - https://kmong.com/prices/%EB%B4%87-%EC%B1%97%EB%B4%87
- **시장 단가**:
  - 최저: 5,000원~1만원 (크몽, 단순 명령어 1~2개짜리 기본 봇)
  - 평균: 5만~15만원 (커스텀 명령어 10개 내외, 역할 관리, 알림 기능)
  - 에이전시: 50만~200만원 (NFT 민팅 연동, 트레이딩 알림, 관리자 대시보드 포함)
- **결제 구조**: 1회 개발비 + 서버 호스팅비 별도(크몽 기준 월 5,000원~). 24시간 운영 시 VPS 비용 월 1만~5만원 추가.
- **업계 명칭 변형**: 텔레봇, 디코 봇, 디스코드 관리봇, 텔레그램 자동화 봇

---

### 3. AI 고객상담 챗봇 (LLM API 연동)

- **한 줄 정의**: OpenAI GPT 또는 Anthropic Claude API를 연동해 자연어로 고객 상담이 가능한 웹·앱 내장 챗봇. 기업 고객센터 대체 또는 보조 용도.
- **바이브코딩 가능 여부**: 높음. API 연동 + 프론트엔드 채팅 UI가 핵심이며, 바이브코딩으로 MVP 1~2일 완성 가능. 다만 프롬프트 설계 및 안전장치는 사람 손이 필요.
- **출처 URL**:
  - https://kmong.com/prices/ai-gpt-%EC%B1%97%EB%B4%87
  - https://kmong.com/gig/556598
  - https://kmong.com/gig/655316
  - https://blog.wishket.com/ai-chatbot-development-cost/
  - https://soomgo.com/prices/%EC%B1%97%EB%B4%87-%EA%B0%9C%EB%B0%9C
- **시장 단가**:
  - 최저: 15만~20만원 (크몽, 기본 GPT API 연동 + 단순 UI)
  - 평균: 30만~60만원 (크몽 기준, GPT-4 기반, 프롬프트 커스터마이징, DB 연동 포함 STANDARD~DELUXE 패키지)
  - 숨고 평균: 100만원 (최저 60만, 최고 200만)
  - 에이전시: 300만~1,000만원 (위시켓 기준 단순 대화형 평균)
- **결제 구조**: 개발비 1회성 + API 사용료(OpenAI 종량제) 클라이언트 부담 또는 월정액 SaaS형. GPT-4o 기준 약 $2.5/1M input tokens.
- **업계 명칭 변형**: AI 상담봇, GPT 챗봇, 인공지능 고객응대, LLM 챗봇, 대화형 AI

---

### 4. RAG 기반 사내 문서 Q&A 시스템

- **한 줄 정의**: 기업 내부 문서(PDF, 사내 위키, 규정집 등)를 벡터DB(Pinecone, Weaviate, ChromaDB 등)에 임베딩해 LLM이 검색 후 답변하는 지식 검색 시스템.
- **바이브코딩 가능 여부**: 중간~높음. LangChain/LlamaIndex 등 프레임워크로 기본 파이프라인은 바이브코딩으로 빠르게 구성 가능. 단, 문서 전처리·청킹 전략·검색 품질 튜닝은 도메인 지식 필요.
- **출처 URL**:
  - https://yozm.wishket.com/magazine/ (RAG 기반 사내 지식 챗봇 구축 사례)
  - https://www.wishket.com/project/similar-case-search/share/vA84Jb4ZEgvhbofq/
  - https://www.wishket.com/project/150552/
  - https://www.makebot.ai/blog/gieobi-2025nyeone-rag-siseutemeul-seontaeghaneun-juyo-iyu-gisuljeog-bunseog
  - https://blog.wishket.com/ai-chatbot-development-cost/
- **시장 단가**:
  - 최저: 50만~100만원 (소규모, 단일 문서 타입, 오픈소스 벡터DB 활용)
  - 평균: 300만~1,000만원 (위시켓 기준 단순~중급 AI 챗봇 범위, 문서 파이프라인 포함)
  - 에이전시: 1,000만~5,000만원 (전사 문서 연동 + 관리자 대시보드 + 권한 관리 포함)
  - 위시켓 AI 챗봇 프로젝트 평균: 2,420만원 (최소 100만, 최대 1억)
- **결제 구조**: 개발비 1회성 + 벡터DB 호스팅 월정액(Pinecone 무료 티어 존재, 유료 $70~/월) + LLM API 사용료.
- **업계 명칭 변형**: 사내 챗봇, 지식 챗봇, 문서 검색 AI, 기업 지식관리 봇, Knowledge Base Chatbot

---

### 5. AI 자동화 에이전트 맞춤 개발

- **한 줄 정의**: LLM이 도구(Tool)를 사용해 여러 단계 작업을 자율 실행하는 시스템. 이메일 자동 분류, 리포트 생성, 데이터 수집·정리 등 반복 업무 자동화. MCP/AutoGen/LangGraph 등 활용.
- **바이브코딩 가능 여부**: 중간. 에이전트 프레임워크(LangGraph, CrewAI) 보일러플레이트는 바이브코딩 적합. 단, 멀티 툴 연동·에러 핸들링·보안 설계는 숙련도 필요.
- **출처 URL**:
  - https://brunch.co.kr/@b8f8683a622d44b/169
  - https://kmong.com/gig/537399
  - https://kmong.com/prices/ai-%EC%8B%9C%EC%8A%A4%ED%85%9C-%EC%84%9C%EB%B9%84%EC%8A%A4
  - https://blog.wonderslab.kr/enterprise-ai-cost-strategy
  - https://aiheroes.ai/community/284
- **시장 단가**:
  - 최저: 10만~50만원 (크몽 바이브코딩 개발자, 단순 자동화 1~2개 워크플로우)
  - 평균 (프리랜서): 50만~200만원 (위시켓/숨고, 웹 크롤링+API 연동+자동 리포트 수준)
  - PoC 단계 (에이전시): 1,500만~3,500만원 (6~8주, 단일 툴 연동, 기본 시나리오)
  - MVP 단계: 3,000만~8,000만원 (10~14주, 다중 툴 연동, 어드민 포함)
  - 프로덕션: 8,000만~2억원+ (12~20주+, 권한 모델·감사 로그·다계정)
  - 운영비: 월 30만~300만원+
- **결제 구조**: 단계별 마일스톤 선불 또는 월 유지보수 계약. 대기업은 연간 유지보수 계약(AMC) 형태.
- **업계 명칭 변형**: AI 에이전트, 업무자동화 봇, AI RPA, 워크플로우 자동화, 맞춤형 AI 솔루션

---

### 6. AI 이미지·영상 생성 연동 서비스

- **한 줄 정의**: Stable Diffusion, DALL-E, Midjourney API, fal.ai, Kling 등을 연동해 사용자가 텍스트/이미지 입력 시 AI 이미지·영상을 생성·반환하는 서비스. 썸네일 자동 생성, 상품 이미지 변환, 영상 편집 자동화 등에 활용.
- **바이브코딩 가능 여부**: 높음. 대부분 REST API 연동이므로 바이브코딩으로 프론트엔드+백엔드 빠른 구성 가능. ComfyUI API 연동도 Python 스크립트 수준.
- **출처 URL**:
  - https://aws.amazon.com/ko/blogs/tech/voyagerx-video-gen-pipline-using-comfyui-workflow/
  - https://kmong.com/gig/537399 (AI 에이전트/자동화/GPT/MCP 등)
  - https://www.alchera.ai/resource/blog/ai-system-implementation-cost
  - https://brunch.co.kr/@macga/70
- **시장 단가**:
  - 최저: 10만~30만원 (단순 Stable Diffusion API 연동 웹앱, 크몽 프리랜서)
  - 평균: 50만~200만원 (프롬프트 입력 UI + 이미지 생성 + 저장/다운로드 기능)
  - 영상 생성 연동 포함: 200만~500만원 (Kling/Sora API, 진행 상태 표시, 다운로드)
  - 에이전시 (상용 서비스 수준): 1,000만~5,000만원 (로그인·크레딧 시스템·CDN 포함)
  - API 사용료 별도: Stable Diffusion 3 기준 약 $0.065/장, Kling 등 영상 생성은 분당 $0.5~수달러
- **결제 구조**: 개발비 1회성 + API 종량제(클라이언트 부담 또는 서비스 내 크레딧 판매). SaaS화 시 월정액 구독 모델.
- **업계 명칭 변형**: AI 이미지 생성 서비스, 텍스트-투-이미지, AI 영상 생성, Generative AI 서비스, AI 아트 플랫폼

---

## 단가 요약표

| 중분류 | 크몽(프리랜서) | 숨고/위시켓 중형 | 에이전시 |
|--------|--------------|----------------|---------|
| 카카오톡 챗봇 | 1.5만~30만원 | 50만~200만원 | 100만~500만원 |
| 텔레그램/디스코드 봇 | 5천원~15만원 | 20만~100만원 | 50만~200만원 |
| AI 고객상담 챗봇(LLM) | 15만~60만원 | 100만~500만원 | 300만~1,000만원 |
| RAG 사내 문서 Q&A | 50만~200만원 | 300만~2,000만원 | 1,000만~5,000만원 |
| AI 자동화 에이전트 | 10만~200만원 | 300만~8,000만원 | 1,500만~2억원+ |
| AI 이미지/영상 생성 연동 | 10만~100만원 | 100만~500만원 | 1,000만~5,000만원 |

---

## 시장 기회 메모

- **바이브코딩 진입 포인트**: 텔레그램/디스코드 봇, AI 고객상담 챗봇은 개발 난이도 대비 크몽 단가가 낮음 → 바이브코딩으로 제작 속도 3~5배 향상 시 마진율 극대화 가능
- **RAG 시스템**: 시장 평균 단가가 높고(위시켓 평균 2,420만원) 수요 증가 중. 바이브코딩으로 템플릿화하면 반복 수주 가능
- **AI 에이전트**: 단가 범위가 넓어 프리랜서~에이전시 모두 포지셔닝 가능. PoC 1,500만~3,500만원이 현실적 첫 수주 목표
- **가격 하향 트렌드**: LLM API 비용 지속 하락 + 오픈소스 도구 확산으로 시장 전체 단가 하향 압력. 스피드와 품질로 차별화 필수

---

## 출처 목록

- https://kmong.com/prices/%EB%B4%87-%EC%B1%97%EB%B4%87
- https://kmong.com/prices/ai-gpt-%EC%B1%97%EB%B4%87
- https://kmong.com/prices/ai-%EC%8B%9C%EC%8A%A4%ED%85%9C-%EC%84%9C%EB%B9%84%EC%8A%A4
- https://soomgo.com/prices/%EC%B1%97%EB%B4%87-%EA%B0%9C%EB%B0%9C
- https://soomgo.com/prices/%EC%9D%B8%EA%B3%B5%EC%A7%80%EB%8A%A5-%EA%B0%9C%EB%B0%9C
- https://blog.wishket.com/ai-chatbot-development-cost/
- https://blog.wishket.com/chatbot-development-type-production-cost/
- https://www.wishket.com/project/similar-case-search/share/vA84Jb4ZEgvhbofq/
- https://brunch.co.kr/@b8f8683a622d44b/169
- https://aiheroes.ai/community/284
- https://blog.wonderslab.kr/enterprise-ai-cost-strategy
- https://www.alchera.ai/resource/blog/ai-system-implementation-cost
- https://i.kakao.com/pricing
- https://www.kakaocorp.com/page/detail/9756

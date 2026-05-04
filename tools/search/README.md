# tools/search — 깊은 검색 (perplexity + 1차 자료 + 플랫폼별 deep)

> 한 쿼리 → perplexity 답변 + 모든 출처 자동 fetch (YouTube transcript 포함) → 통합본.
> 추가로 Reddit / HN / GitHub / Twitter 플랫폼 deep dive 모듈 독립 사용 가능.

## 메인 흐름 (`dive.py`)

```bash
python tools/search/dive.py "쿼리"
```

→ perplexity sonar-pro → citation 자동 분리 (YouTube transcript + 일반 웹 본문) → `raw/sources/dive_{slug}_{date}.md` 1장.

## 파일 (8개)

| 파일 | 역할 |
|---|---|
| **dive.py** | 메인 entry — perplexity + 모든 citation 병렬 fetch + 통합 마크다운 |
| `pplx.py` | perplexity API wrapper (단독 호출 가능) |
| `browse.py` | 단일 URL 본문 추출 (BeautifulSoup, 5000자 발췌) |
| `yt.py` | YouTube transcript (한국어 우선, 영어 fallback) |
| **reddit_dive.py** | Reddit search + 게시글/댓글 트리 (무인증 JSON endpoint) |
| **hn_dive.py** | HN search + 댓글 트리 (Algolia + Firebase) |
| **github_dive.py** | GitHub repo 검색 + README + issue 본문 (옵션 GITHUB_TOKEN) |
| **twitter_dive.py** | Twitter/X best-effort (nitter scrape, ⚠️ 작동 보장 X) |

## 플랫폼별 deep 사용 (독립)

### Reddit (★ 가장 안정)

```bash
python tools/search/reddit_dive.py search "AI coding agent" --sub solopreneur --n 25
python tools/search/reddit_dive.py fetch "https://reddit.com/r/.../comments/..." --comments 50
```

무인증, rate limit 60/min. 전체 Reddit 또는 특정 subreddit 검색. 게시글 본문 + 댓글 트리 (depth 5).

### Hacker News (★ 가장 깊음)

```bash
python tools/search/hn_dive.py search "vibe coding" --n 20 --sort byPopularity
python tools/search/hn_dive.py fetch 38123456 --comments 80 --depth 4
```

무인증, rate limit 관대. Algolia HN search → 게시글 ID → Firebase로 댓글 재귀.

### GitHub

```bash
python tools/search/github_dive.py search "spec driven development" --lang typescript --n 10
python tools/search/github_dive.py readme anthropics/claude-code
python tools/search/github_dive.py issues anthropics/claude-code --state open --n 20
```

무인증 = **60/hr** rate limit. `.env`에 `GITHUB_TOKEN=...` 박으면 5000/hr.

### Twitter/X (⚠️ best-effort)

```bash
python tools/search/twitter_dive.py search "claude code" --n 20
```

2026 현재 X API 막힘 + nitter 인스턴스 대부분 폐쇄. 작동 보장 X. 안 되면 **perplexity citation의 X 결과**에 의존.

## 비용

| 도구 | 비용 |
|---|---|
| perplexity sonar-pro 1쿼리 | ~$0.006 |
| browse / yt / reddit / hn / github (무인증) | 무료 |
| GitHub (token 인증) | 무료 (5000/hr) |
| Twitter (nitter) | 무료 (작동 시) |

`tools/cost/cost_log.py` 가 모든 호출 자동 로깅 (`.cost_log.jsonl`).

**1회 dive (perplexity + citation fetch) ≈ $0.01.**

## 의존성

```bash
pip install requests beautifulsoup4 yt-dlp
```

(이미 설치됨 2026-05-03)

## 한계 + 노트

- **dive.py 재귀 검색 미구현** — depth ≥ 2 (답변에서 새 질문 자동 도출) 다음 버전.
- **dive.py + 플랫폼 deep 통합 미구현** — 지금은 각 모듈 독립. 통합 옵션 (--reddit / --hn / --github) 다음 버전.
- **Reddit/HN/GitHub** = 깊이 좋음. **Twitter** = 거의 안 됨.
- transcript 없는 영상 / 403 사이트 silent skip.

## 사용 패턴 (권장)

1. **첫 단계**: `dive.py "쿼리"` — 넓은 답 + 일반 출처
2. **Reddit 깊이 필요**: `reddit_dive.py search` 결과 보고 흥미 게시글 → `fetch`
3. **HN 토론 필요**: `hn_dive.py search` → `fetch` (comment tree)
4. **GitHub 코드/이슈**: `github_dive.py search` → `readme` 또는 `issues`
5. **결과 통합**: 사용자가 raw/sources/ 에 통합본 직접 작성 (dive.py 재귀 통합은 다음 버전)

## 향후 (지금 X)

- dive.py에 `--reddit-deep N` / `--hn-deep N` / `--github-deep` 옵션 추가
- 재귀 검색 (depth 2-3, 답변에서 새 질문 자동 도출)
- 결과 캐시 (같은 쿼리 24h 재사용)

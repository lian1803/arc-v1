# Wave 2 CTO↔CDO 크로스 토론 합의문
# 소상공인 네이버 플레이스 영업툴

작성일: 2026-03-26

---

## 토론 기록

---

### 쟁점 1: CSS 방향 — Tailwind 추가 vs 기존 CSS 확장

**CTO 입장:**
기존 코드베이스를 확인하지 않은 상태에서 Tailwind를 무조건 추가하는 건 위험하다. 이유는 세 가지.
첫째, 기존 style.css에 커스텀 클래스가 있다면 Tailwind의 리셋(Preflight)이 충돌을 일으킨다.
둘째, CDN 개발용 Tailwind(Play CDN)는 JS 런타임이 필요하고 용량이 크다. 로컬 툴이라 성능 크리티컬하진 않지만 불필요한 의존성이다.
셋째, 페이지가 index/result/history/loading 4개 수준이다. 이 규모에서 Tailwind 도입은 오버킬.

CDO가 요청한 컴포넌트들(배지, 탭, 아코디언, 진행 바)은 전부 Vanilla CSS로 50줄 이내 구현 가능하다. Tailwind 없어도 된다.

**CDO 반론:**
Tailwind 없이 직접 CSS를 짜면 네이버 그린(#03C75A), 카카오 옐로우(#FEE500), 경고 빨강(#FF4757) 등 팔레트 관리가 분산된다. CSS 변수(Custom Properties)로 대체 가능하긴 하지만, CDO가 wave1_cdo.md에 "Tailwind 클래스로 직접 구현"이라고 명시한 이유는 일관성 때문이다.

단, CTO 우려처럼 기존 style.css와 충돌이 생기면 안 된다.

**합의:**
Tailwind CDN을 추가하되, Tailwind Preflight(CSS 리셋)는 비활성화한다.
방법: `<link>` CDN 대신 `<script src="https://cdn.tailwindcss.com">` + 인라인 설정으로 `preflight: false` 설정.

```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    corePlugins: {
      preflight: false,  // 기존 style.css 충돌 방지
    },
    theme: {
      extend: {
        colors: {
          'naver-green': '#03C75A',
          'kakao-yellow': '#FEE500',
          'priority-red': '#FF4757',
          'priority-orange': '#FFA502',
          'priority-gray': '#A4A4A4',
        }
      }
    }
  }
</script>
```

기존 style.css는 건드리지 않는다. 신규 컴포넌트(배지, 탭, 메시지 카드 등)만 Tailwind 클래스로 작성.
구조적 레이아웃(기존 헤더, 내비게이션)은 기존 CSS 그대로.

---

### 쟁점 2: 메시지 탭 구현 — 서버사이드 전달 방식 확정

**CDO 질문:**
영업 메시지 4개 탭 데이터를 서버사이드 렌더링으로 전달하면 탭 전환 시 페이지 재로드 없이 되나?

**CTO 답변:**
된다. 이게 올바른 방향이다.

메커니즘 설명:
- FastAPI에서 result.html 렌더링 시, `messages` 딕셔너리를 Jinja2 컨텍스트에 함께 전달
- Jinja2가 1차~4차 메시지 텍스트를 HTML에 미리 렌더링해서 각 탭 패널 `<div>`에 삽입
- 탭 전환은 순수 JS로 `display:none/block` 토글 — 서버 요청 없음

예시 구조:
```html
<!-- Jinja2가 서버에서 렌더링 -->
<div id="tab-panel-1" class="tab-panel">
  {{ messages.first.text }}
</div>
<div id="tab-panel-2" class="tab-panel hidden">
  {{ messages.second }}
</div>
```

```javascript
// 탭 전환: 서버 요청 없이 DOM 토글만
function switchTab(tabIndex) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
  document.getElementById(`tab-panel-${tabIndex}`).classList.remove('hidden');
}
```

AJAX 방식(별도 API 호출)은 불필요하다. CDO 선호안이 맞다.
단, `messages.first`는 A/B/C 버전 3개를 모두 포함해서 내려줘야 한다. JS에서 버전 토글도 동일한 방식으로 처리.

**JS 파일 분리 여부:**
기존 코드가 인라인 `<script>` 방식이면 일단 그대로 따른다(기존 패턴 유지 원칙). 다만 result.html은 탭 전환 + 복사 + 편집 + 아코디언 등 JS 로직이 많으므로 `static/js/result.js` 파일로 분리하는 게 유지보수에 유리하다. FE 작업자가 판단해서 결정.

---

### 쟁점 3: 클립보드 복사 폴백 처리

**CDO 질문:**
`navigator.clipboard.writeText()` — HTTP 환경에서 동작 안 한다. 폴백 어떻게 처리하나.

**CTO 답변:**
로컬 실행 환경(`http://localhost`)에서는 Clipboard API 동작한다. 로컬 전용 도구이므로 당장 문제없다.

단, 안전하게 폴백을 넣어라. 구현 방식:

```javascript
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    // 폴백: execCommand (deprecated이지만 HTTP 환경 대응)
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    const success = document.execCommand('copy');
    document.body.removeChild(textarea);
    return success;
  }
}
```

버튼 상태 변경 (CDO 요청 반영):
```javascript
async function handleCopyBtn(btn, text) {
  const success = await copyToClipboard(text);
  if (success) {
    const original = btn.textContent;
    btn.textContent = '복사됨 ✓';
    btn.disabled = true;
    setTimeout(() => {
      btn.textContent = original;
      btn.disabled = false;
    }, 1500);
  }
}
```

이 함수 하나를 `result.js`에 정의하고, 카카오용/SMS용 버튼 모두 이 함수 재사용.

---

### 쟁점 4: 점수 시각화 — Chart.js vs Pure CSS

**CTO 입장:**
Chart.js CDN 추가는 허용 범위지만, 7개 항목 가로 막대 차트는 Pure CSS로 충분히 구현된다. Chart.js를 쓰면 캔버스 기반이라 반응형 처리가 복잡해지고, 항목명 + 점수 텍스트를 커스텀하기 위해 Chart.js 설정이 오히려 더 장황해진다.

CDO가 요청한 스펙:
- 항목명 + 점수/100 텍스트
- 막대 길이 (점수에 비례)
- 60점 미만 빨강/주황, 60점 이상 그린
- 페이지 로드 시 0에서 채워지는 CSS transition 애니메이션

이건 Pure CSS + Vanilla JS로 Chart.js보다 더 깔끔하게 된다.

**CDO 동의:**
Pure CSS가 맞다. 경쟁사 비교 슬라이드가 PPT에 있는데 웹 차트까지 Chart.js 쓰면 의존성이 늘어난다. 막대 차트가 "정확한 데이터 시각화"보다 "한눈에 약한 항목 파악"이 목적이므로 CSS로 충분.

**합의: Pure CSS 가로 막대 차트 채택**

구현 스펙:
```html
<!-- Jinja2 템플릿에서 렌더링 -->
{% for item in score_items %}
<div class="score-row">
  <span class="score-label">{{ item.name }}</span>
  <div class="score-bar-bg">
    <div class="score-bar {{ 'bar-danger' if item.score < 40 else 'bar-warning' if item.score < 60 else 'bar-good' }}"
         style="--target-width: {{ item.score }}%">
    </div>
  </div>
  <span class="score-num">{{ item.score }}/100</span>
</div>
{% endfor %}
```

```css
.score-bar {
  height: 20px;
  width: 0%;
  border-radius: 4px;
  transition: width 0.6s ease-out;
}
.score-bar.bar-danger  { background: #FF4757; }
.score-bar.bar-warning { background: #FFA502; }
.score-bar.bar-good    { background: #03C75A; }
```

```javascript
// 페이지 로드 후 애니메이션 트리거
window.addEventListener('load', () => {
  document.querySelectorAll('.score-bar').forEach(bar => {
    const target = bar.style.getPropertyValue('--target-width');
    bar.style.width = target;
  });
});
```

Chart.js CDN 추가 안 함. 의존성 최소화.

---

### 쟁점 5: 아코디언 (진단 요약 섹션 기본 접힘)

**CDO 요청:**
진단 요약 섹션 기본 접힘 상태. "진단 상세 보기 ▼" 클릭해서 펼침.

**CTO 답변:**
HTML 네이티브 `<details>/<summary>` 사용. JS 없음.

```html
<details class="diagnosis-accordion">
  <summary class="accordion-trigger">
    진단 상세 보기 <span class="arrow">▼</span>
  </summary>
  <div class="accordion-content">
    <!-- 점수 바 차트 -->
  </div>
</details>
```

CSS로 열림 상태 화살표 회전:
```css
details[open] .arrow { transform: rotate(180deg); }
.arrow { transition: transform 0.2s; display: inline-block; }
```

기본값이 `<details>` 태그는 닫힌 상태. CDO 요청 그대로 반영. JS 구현 복잡도 없음.

---

### 쟁점 6: CDO 확인 사항 6개 전체 답변

**CDO 질문 1 — Tailwind 현재 포함 여부:**
기존 코드에 Tailwind 없을 가능성 높다(FastAPI + Jinja2 기본 셋업). 쟁점 1 합의대로 CDN으로 추가하되 Preflight 비활성화.

**CDO 질문 2 — 메시지 결과 result.html 전달 방법:**
서버사이드 렌더링 방식 채택. crawl.py에서 크롤링/진단 완료 시 `message_generator.generate_all()` 호출 → 결과를 Jinja2 컨텍스트에 포함 → result.html 렌더링. AJAX 불필요.
데이터 구조:
```python
# routers/crawl.py에서 result.html 렌더링 시
return templates.TemplateResponse("result.html", {
    "request": request,
    "diagnosis": diagnosis_data,
    "messages": {
        "first": {"version": "A", "text_a": "...", "text_b": "...", "text_c": "...", "auto_version": "A"},
        "second": "...",
        "third": "...",
        "fourth": {"version_hold": "...", "version_expensive": "...", "version_diy": "..."}
    },
    "competitor": competitor_data,
    "score_items": score_items_list,
})
```

**CDO 질문 3 — 탭 전환 Vanilla JS, 파일 분리:**
쟁점 2에서 답변 완료. 기존 인라인 패턴이면 유지, 신규 JS가 많으면 `static/js/result.js` 분리. FE 작업자 판단.

**CDO 질문 4 — 클립보드 복사 API 호환성:**
쟁점 3에서 답변 완료. localhost 환경은 OK. `execCommand` 폴백 포함해서 구현.

**CDO 질문 5 — history.html 필터링 방식:**
클라이언트사이드 JS 방식 채택. 서버에서 전체 목록을 한 번에 렌더링하고, JS로 DOM 숨기기/보이기.

이유:
- 히스토리가 수백 건을 넘지 않는다 (1인 영업자 도구, 일 1~5건 진단).
- 페이지 리로드 방식은 필터 클릭마다 서버 요청 + 화면 깜빡임.
- `<div data-priority="1순위" data-category="미용실">` 속성으로 필터 구현.

```javascript
function filterHistory(priority) {
  const cards = document.querySelectorAll('.business-card');
  let count = 0;
  cards.forEach(card => {
    const match = priority === 'all' || card.dataset.priority === priority;
    card.style.display = match ? 'block' : 'none';
    if (match) count++;
  });
  document.getElementById('filter-count').textContent = `(${count}개)`;
}
```

**CDO 질문 6 — 우선순위 태그 수동 변경 저장:**
`PATCH /api/businesses/{id}/priority` 엔드포인트 신규 추가 확정.

```python
# routers/history.py 또는 별도 routers/priority.py에 추가
@router.patch("/api/businesses/{history_id}/priority")
async def update_priority(history_id: int, priority: str, db: AsyncSession = Depends(get_db)):
    # DiagnosisHistory.sales_priority 컬럼 업데이트
    ...
```

태그 클릭 → 드롭다운 선택 → JS `fetch PATCH` 호출 → 서버 저장 → UI 즉시 반영 (페이지 리로드 없음).

---

## 최종 합의 요약

| 항목 | 합의 결정 |
|------|-----------|
| CSS 방향 | Tailwind CDN 추가 (Preflight 비활성화). 기존 style.css 유지. 신규 컴포넌트만 Tailwind 클래스 사용 |
| 메시지 탭 전달 | 서버사이드 렌더링. Jinja2 컨텍스트에 messages 딕셔너리 포함. 탭 전환은 JS DOM 토글 (서버 요청 없음) |
| 클립보드 복사 폴백 | `navigator.clipboard.writeText()` 우선, `document.execCommand('copy')` 폴백 포함. 함수 1개로 통일 |
| 점수 시각화 | Pure CSS 가로 막대 차트. Chart.js CDN 추가 안 함. CSS transition 애니메이션으로 채움 효과 |
| 아코디언 | HTML 네이티브 `<details>/<summary>`. JS 없음. 기본 접힘 상태 |
| history 필터 | 클라이언트사이드 JS (DOM 숨기기/보이기). 서버 쿼리 방식 아님 |
| 우선순위 수동 저장 | `PATCH /api/businesses/{id}/priority` 신규 엔드포인트 추가 확정 |
| 탭 JS 파일 | 기존 인라인 패턴 확인 후 결정. 신규 JS 많으면 `static/js/result.js` 분리 |

---

## FE 작업자(Wave 3)에게 전달 사항

1. **기존 HTML 파일 검토 먼저**: `templates/result.html`, `templates/history.html` 기존 구조 파악 후 최소한으로 수정.
2. **Tailwind config 스니펫**: 위 합의문의 `tailwind.config` 코드 그대로 사용. 커스텀 색상명 동일하게.
3. **`copyToClipboard` 함수**: 합의문의 폴백 포함 버전 그대로 사용.
4. **점수 바 차트**: `--target-width` CSS 변수 방식. `window.load` 이벤트에서 width 적용.
5. **메시지 데이터 바인딩**: Jinja2 `{{ messages.first.text_a }}` 방식으로 HTML에 직접 삽입.
6. **우선순위 PATCH API**: BE에서 엔드포인트 만들면 FE에서 `fetch`로 호출. 응답 성공 시 태그 배경색만 바꿔주면 됨.

## BE 작업자(Wave 3)에게 전달 사항

1. **crawl.py result 렌더링**: 크롤링 완료 시 `message_generator.generate_all()` 호출 후 result.html 컨텍스트에 포함.
2. **messages 딕셔너리 구조**: 위 합의문 `CDO 질문 2` 답변의 구조 그대로 구현.
3. **PATCH 엔드포인트**: `DiagnosisHistory.sales_priority` 컬럼 업데이트. 유효값: `"1순위"`, `"2순위"`, `"패스"`.
4. **score_items 리스트**: `[{"name": "사진", "score": 45}, ...]` 형태로 Jinja2 컨텍스트 전달. result.html에서 for 루프로 막대 차트 렌더링.

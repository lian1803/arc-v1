# HERO_PLAN — 제니스 미디어 파트너스

## 1. Opening Shot
검은 화면. 화면 중앙 하단에 희미한 수평선 구분선(얇은 navy glow). 화면 전체를 덮는 짙은 다크 네이비 안개 그라데이션. 아무것도 보이지 않는다. 0.5초 후 — 화면 오른쪽 상단에서 얇은 빛 기둥(glow-line)이 느리게 회전 시작.

## 2. Motion Sequence
- 0.0s: 칠흑 같은 다크 네이비. 수평선 희미하게.
- 0.5s: 화면 우상단에서 glow-line 빔 1개 등장, 느린 회전.
- 1.2s: 빔이 화면을 가로질러 좌하단을 향해 쏜다. 안개가 빛 경로를 따라 옅어짐.
- 2.0s: 빔이 처음 닿는 지점 — 작은 텍스트 노드들(사업체 이름들)이 빛 앞에서 깜박이며 드러남.
- 3.0s: 빔이 계속 회전하며 여러 텍스트 노드들을 순차적으로 조명. 카메라 위로 천천히 이동 시작.

## 3. Text Reveal
- progress 0.0: 화면 하단에 서브카피 "보이지 않는 가게를 보이게 만듭니다" — opacity 0
- progress 0.35: 서브카피 line-by-line reveal (clip-path: inset(0 100% 0 0) → 0)
- progress 0.65: 타이틀 "ZENITH" — 대형 타이포, 글자별 translateY(-30px)→0 stagger 0.05
- progress 0.85: "MEDIA PARTNERS" — 서브 타이틀, letter-spacing 넓어지며 등장
- progress 1.0: CTA 버튼 scale(0.8)→1 + opacity reveal

## 4. Camera Path
| progress | pos (x,y,z) | lookAt (x,y,z) |
|---|---|---|
| 0.0 | (0, -2, 8) | (0, 0, 0) |
| 0.3 | (0.5, 0, 6) | (0, 0.5, 0) |
| 0.6 | (0, 2, 5) | (0, 1, 0) |
| 0.85 | (-0.3, 4, 4) | (0, 2, 0) |
| 1.0 | (0, 6, 4) | (0, 3, 0) |

## 5. Effects
- **glow-line** (primary): 등대 빔 2개 (왼쪽/오른쪽 비대칭), 색상 #fbbf24(골드), 느린 회전 애니메이션. 이유: 등대 빔 = 핵심 은유의 시각화
- **bloom-stack** (additive): glow-line 위에 블룸 레이어 추가, 빔 주변 광원 번짐. 이유: 빛의 물리적 현실감
- **camera-scroll** (structure): 스크롤 progress에 카메라 경로 바인딩. 이유: "카메라가 위로 올라가며 등대를 발견"하는 서사

## 6. Technology
three_js_code — 3D 씬(glow-line 빔, 카메라), GSAP ScrollTrigger + Lenis(camera-scroll). CSS motion으로 텍스트 오버레이.

## 7. Brand Reveal Moment
progress 0.65 — 카메라가 충분히 위로 올라온 시점, 등대 빔이 화면 중앙을 비출 때 "ZENITH" 타이포 등장. 브랜드가 등대 그 자체임을 암시.

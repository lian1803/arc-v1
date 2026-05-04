# 2026-05 루트 청소 archive

> 2026-05-04 ARC 루트 `.tmp_*` 30개 일괄 정리. luna §14 Temp-Is-Temp 정합 후행 처리.
> 보존만. 참조 X.

<details>
<summary><b>pplx_consolidated/</b> — Perplexity 호출 (통합본 있음)</summary>

이미 `raw/sources/perplexity_*.md` 4개에 통합됨. 스크립트는 호출 패턴 참고용.

- `.tmp_pplx.py`, `.tmp_pplx2.py` → `raw/sources/perplexity_arc_orchestrator_2026-04-30.md`
- `.tmp_pplx_develop.py` + `.tmp_pplx_out_dev/` → `raw/sources/perplexity_develop_2026-05-03.md`
- `.tmp_pplx_meta.py` + `.tmp_pplx_out_meta/` → `raw/sources/perplexity_meta_buildgap_2026-05-03.md`
- `.tmp_pplx_solopreneur.py` + `.tmp_pplx_out_solo/` → `raw/sources/perplexity_solopreneur_standard_2026-05-03.md`
- `.tmp_pplx_out/` — 1차 raw json (atlas/payment/carry 쿼리 3개)

</details>

<details>
<summary><b>pplx_unconsolidated/</b> — Perplexity 호출 (결과 미통합)</summary>

4-29~30 작업. raw/sources/에 통합본 없음. 결과 손실 방지 목적 보존.

- `atlas` — Stripe Atlas 가입 절차
- `danggn` — 당근 lead 추출
- `kakao`, `kakao2` — 카카오 알림톡 / 채널
- `pains` — 자영업 pain 발굴
- `toss` — Toss 결제 onboarding
- `v1v2` — v1/v2 비교

필요 시 `raw/sources/`로 통합 작업.

</details>

<details>
<summary><b>thumb_grab/</b> — 유튜브 썸네일 grabber (5/4 실험)</summary>

`tools/image/_out/factory_v5_assets/` 캐시는 별도 보존됨 (NEXT.md L32). 본 폴더는 grabber 실험만.

- 스크립트: `.tmp_thumb_grab.py`, `.tmp_thumb_grab_wide.py`
- 결과 폴더: `.tmp_thumbs_topyt/`, `.tmp_thumbs_wide/`, `.tmp_lian_thumbs/`
- fetch: `.tmp_yt_search.json`, `.tmp_gh_thumb*.json` (3), `.tmp_reddit_thumb.json`, `.tmp_gh_readme.md`
- 로그: `.tmp_thumb_grab.log`

</details>

<details>
<summary><b>logs/</b> — 빌드 로그</summary>

factory_v1/all, v4, v5, topyt_v2, wide, dive_kr_senior, dive_thumb_pipeline.

</details>

<details>
<summary><b>misc/</b> — 기타</summary>

`.tmp_hook_test.py` (4-30 hook 실험).

</details>

---

## 자동 차단 (이후 발생 방지)

`.claude/hooks/route_root_writes.py` 가 PreToolUse Write 발동 시 ARC 루트 화이트리스트 외 신규 파일 차단. `.tmp_*` 는 자동으로 `archive/scratch/YYYY-MM/` 로 안내.

룰: `.claude/rules/file-routing.md`.

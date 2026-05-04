"""run_patterns.py — 5 패턴 진화 알고리즘 + 6 항목 메타 fire."""
import os, sys, json, re
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
OUT = ROOT / "projects" / "youtube_automation_demo"
OUT.mkdir(exist_ok=True, parents=True)

GEMS_PATH = Path(__file__).parent / "gems_base.txt"
if not GEMS_PATH.exists() or not GEMS_PATH.read_text(encoding="utf-8").strip():
    raise FileNotFoundError(
        f"Gems base prompt 비어있음/없음. 시니어 채널 페르소나 prompt를 여기 채워: {GEMS_PATH}"
    )
GEMS = GEMS_PATH.read_text(encoding="utf-8")
TOPIC = "60대 이후 무릎 통증 — 음식 1가지와 습관 1가지"
LENGTH = "공백 제외 350-500 자 (1-2분 영상 분량)"

GK = os.environ["GEMINI_API_KEY"]
AK = os.environ["ANTHROPIC_API_KEY"]
PK = os.environ["PERPLEXITY_API_KEY"]


def gemini(prompt, model="gemini-2.5-flash"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GK}"
    r = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=120)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def claude(prompt, model="claude-sonnet-4-5"):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": AK, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model, "max_tokens": 4000, "messages": [{"role": "user", "content": prompt}]},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def perplexity(query):
    r = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {PK}", "Content-Type": "application/json"},
        json={"model": "sonar", "messages": [{"role": "user", "content": query}]},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def base(extra=""):
    return f"{GEMS}\n\n레퍼런스: {TOPIC}\n분량: {LENGTH}\n{extra}"


def run_a():
    text = gemini(base())
    (OUT / "A_pattern.txt").write_text(text, encoding="utf-8")
    print(f"A: {len(text)} chars")


def run_b():
    draft = gemini(base())
    critique = claude(
        f"한국 시니어 유튜브 스크립트 평가 + 수정 제안. 기준: retention/cliffhanger/TTS 적합성/한글 숫자 변환/의료법 회피.\n\n{draft}"
    )
    revised = gemini(base(f"\n다음 비평 반영 재작성:\n{critique}\n\n원본:\n{draft}"))
    (OUT / "B_pattern.txt").write_text(revised, encoding="utf-8")
    (OUT / "B_critique_log.md").write_text(
        f"# B Self-Critique\n\n## Draft\n{draft}\n\n## Critique\n{critique}\n\n## Revised\n{revised}",
        encoding="utf-8",
    )
    print(f"B: {len(revised)} chars")


def run_c():
    research = perplexity(f"{TOPIC} 의학적 사실 / 음식 효능 / 습관 효과 / 출처 포함")
    outline = claude(
        f"Lian gems format 따라 outline 짜라. 형식: 서론 hook / 본론 (음식+습관) / 결론 CTA, 각 1-2줄.\n\n리서치:\n{research}"
    )
    draft = gemini(base(f"\nOutline 따라 작성:\n{outline}"))
    final = claude(f"한국 시니어 TTS 톤 / 한글 숫자 / cliffhanger 검수 + 최종 수정 (전체 본문 출력).\n\n{draft}")
    (OUT / "C_pattern.txt").write_text(final, encoding="utf-8")
    (OUT / "C_chain_log.md").write_text(
        f"# C Multi-Agent\n\n## Research\n{research}\n\n## Outline\n{outline}\n\n## Draft\n{draft}\n\n## Final\n{final}",
        encoding="utf-8",
    )
    print(f"C: {len(final)} chars")


def run_d():
    hooks = ["내부고발 (병원에서 절대 먼저 꺼내지 않는 이야기)", "결과미리 (끝까지 보시면 해결법)", "개인사 (저도 같은 경험)"]
    variants = [gemini(base(f"\n서론 분기: {h}")) for h in hooks]
    judged = claude(
        "3 변형 retention 예측 (1-10) + best 1 선택. 응답 첫 줄 'best: N' format.\n\n"
        + "\n\n".join(f"변형 {i+1}: {h}\n{v}" for i, (h, v) in enumerate(zip(hooks, variants)))
    )
    m = re.search(r"best:\s*(\d+)", judged.lower())
    bi = int(m.group(1)) - 1 if m else 0
    best = variants[bi]
    (OUT / "D_pattern.txt").write_text(best, encoding="utf-8")
    log = "# D A/B Parallel\n\n" + "\n\n".join(
        f"## Variant {i+1}: {h}\n{v}" for i, (h, v) in enumerate(zip(hooks, variants))
    ) + f"\n\n## Judge\n{judged}\n\n## Selected: {bi+1}"
    (OUT / "D_judge_log.md").write_text(log, encoding="utf-8")
    print(f"D: {len(best)} chars (var {bi+1})")


def run_e():
    outline = gemini(base("\nOutline ONLY (본문 X). 4 챕터: 서론/본론음식/본론습관/결론, 각 1-2줄."))
    chapters = []
    for ch in ["서론", "본론-음식", "본론-습관", "결론"]:
        c = gemini(base(f"\n전체 outline:\n{outline}\n\n현재 챕터: {ch}만 작성 (80-130자). transition 자연스럽게."))
        chapters.append(c)
    final = "\n\n".join(chapters)
    (OUT / "E_pattern.txt").write_text(final, encoding="utf-8")
    (OUT / "E_outline.md").write_text(
        f"# E Outline-first\n\n## Outline\n{outline}\n\n## Chapters\n\n" + "\n\n---\n\n".join(chapters),
        encoding="utf-8",
    )
    print(f"E: {len(final)} chars")


def gen_meta(p, script):
    raw = claude(
        f"한국 시니어 유튜브 스크립트 (1-2분) 에 대한 5 메타. JSON 만 출력 (다른 텍스트 X):\n"
        f'{{"title": "60자 이하 한글 hook+숫자", "keywords": ["..."], '
        f'"thumbnail_prompt": "영문 fal SD prompt, 의사+무릎+음식", '
        f'"description": "300-500자 한글 SEO+챕터+CTA", '
        f'"pinned_comment": "한줄 engagement"}}\n\n스크립트:\n{script}'
    ).strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    return json.loads(raw)


def run_meta():
    for p in "ABCDE":
        try:
            script = (OUT / f"{p}_pattern.txt").read_text(encoding="utf-8")
            meta = gen_meta(p, script)
            (OUT / f"{p}_metadata.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"{p} meta OK")
        except Exception as e:
            print(f"{p} meta FAIL: {e}")
            (OUT / f"{p}_metadata.json").write_text(
                json.dumps({"error": str(e)}, ensure_ascii=False), encoding="utf-8"
            )


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or "scripts" in a:
        for fn in [run_a, run_b, run_c, run_d, run_e]:
            try:
                fn()
            except Exception as e:
                print(f"FAIL {fn.__name__}: {e}")
    if not a or "meta" in a:
        run_meta()
    print("DONE")

"""run_v3_iterate.py — D 알고리즘 + 쉼표 풍부 + 3 라운드 → best 대본 1."""
import os, sys, json, re, time
from pathlib import Path
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
OUT = ROOT / "projects" / "youtube_automation_demo" / "v3_iter"
OUT.mkdir(exist_ok=True, parents=True)
GK, AK = os.environ["GEMINI_API_KEY"], os.environ["ANTHROPIC_API_KEY"]
GEMS_PATH = Path(__file__).parent / "gems_base.txt"
if not GEMS_PATH.exists() or not GEMS_PATH.read_text(encoding="utf-8").strip():
    raise FileNotFoundError(
        f"Gems base prompt 비어있음/없음. 시니어 채널 페르소나 prompt를 여기 채워: {GEMS_PATH}"
    )
GEMS = GEMS_PATH.read_text(encoding="utf-8")
TOPIC = "60대 이후 무릎 통증 — 음식 1가지와 습관 1가지"
LENGTH = "공백 제외 약 17,000~20,000자 (50~55분 영상)"

COMMA = """🚨 TTS PACING 강제:
- 한 문장 평균 2-3 쉼표 (호흡 단위). 쉼표 0 문장 금지.
- 한글 숫자 (70세→일흔 살, 5분→오 분).
- 매 1500자마다 cliffhanger ('잠시만요', '다음 내용은 절대 놓치면', '여기서 끝이 아닙니다').
- 1인칭 시니어 친근 톤, 짧은 문장."""


def gemini(p, retries=3):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GK}"
    for i in range(retries):
        try:
            r = requests.post(url, json={"contents": [{"parts": [{"text": p}]}],
                "generationConfig": {"maxOutputTokens": 32000, "temperature": 0.95}}, timeout=300)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            if i == retries - 1: raise
            time.sleep(5)


def claude(p, mt=8000):
    r = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": AK, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-5", "max_tokens": mt, "messages": [{"role": "user", "content": p}]},
        timeout=300)
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def cd(t):
    n = t.replace(" ", "").replace("\n", "")
    return t.count(",") / len(n) * 100 if n else 0


def cc(t):
    return len(t.replace(" ", "").replace("\n", ""))


def base(extra=""):
    return f"{GEMS}\n\n주제: {TOPIC}\n분량: {LENGTH}\n{COMMA}\n{extra}"


def r1():
    hooks = [
        "결과미리 (끝까지 보시면 ~ 알게 됩니다 / 데이터 강조)",
        "내부고발 (병원에서 절대 먼저 꺼내지 않는 이야기)",
        "환자스토리 (칠십 대 박순자 할머니 이야기로 시작)",
    ]
    print("[R1] 3 variants...")
    vs = []
    for i, h in enumerate(hooks):
        print(f"  v{i+1}: {h[:30]}")
        t = gemini(base(f"\n서론 hook: {h}\n전체 본문 출력 (공백제외 17,000자 이상)."))
        vs.append({"hook": h, "text": t, "chars": cc(t), "cd": cd(t)})
        (OUT / f"r1_v{i+1}.txt").write_text(t, encoding="utf-8")
        print(f"    {vs[-1]['chars']}자 쉼표 {vs[-1]['cd']:.2f}")
    j = claude("3 변형 평가. 각 retention/TTS적합성/감정 1-10. 첫줄 'best: N'.\n\n"
        + "\n\n".join(f"=== 변형 {i+1} ({v['hook']}) ===\n{v['text'][:8000]}" for i, v in enumerate(vs)),
        mt=4000)
    m = re.search(r"best:\s*(\d+)", j.lower())
    bi = int(m.group(1)) - 1 if m else 0
    (OUT / "r1_judge.md").write_text(j, encoding="utf-8")
    print(f"[R1] winner v{bi+1}")
    return vs[bi]


def r2(w):
    print("[R2] critique + revise...")
    c = claude(f"""풀 50분 대본 평가. 항목별 점수 + 수정 제안:
1. 쉼표 밀도 2. retention 3. 한글 숫자 4. 감정 흐름 5. 의료법 risk 6. 분량 (17000자?)

원본:
{w['text']}""", mt=4000)
    rev = gemini(base(f"\n비평 반영 재작성. 분량 17000~22000자:\n\n{c}\n\n원본:\n{w['text']}"))
    (OUT / "r2_critique.md").write_text(c, encoding="utf-8")
    (OUT / "r2_revised.txt").write_text(rev, encoding="utf-8")
    rec = {"text": rev, "chars": cc(rev), "cd": cd(rev), "hook": "R2-revised"}
    print(f"[R2] {rec['chars']}자 쉼표 {rec['cd']:.2f}")
    return rec


def r3(a, b):
    print("[R3] A vs B...")
    p = ("두 후보 비교. 쉼표 밀도/retention/감정/자연스러움/분량 각 1-10. 첫줄 'final: A' or 'final: B'.\n\n"
        f"=== A ({a['chars']}자 쉼표{a['cd']:.2f}) ===\n{a['text'][:9000]}\n\n"
        f"=== B ({b['chars']}자 쉼표{b['cd']:.2f}) ===\n{b['text'][:9000]}")
    j = claude(p, mt=2500)
    (OUT / "r3_judge.md").write_text(j, encoding="utf-8")
    m = re.search(r"final:\s*([ab])", j.lower())
    pk = "A" if (not m or m.group(1) == "a") else "B"
    f = a if pk == "A" else b
    print(f"[R3] FINAL: {pk}")
    return f, pk


def main():
    t0 = time.time()
    w1 = r1()
    w2 = r2(w1)
    fin, pk = r3(w1, w2)
    (OUT / "winner_full.txt").write_text(fin["text"], encoding="utf-8")
    s = {"winner": pk, "chars": fin["chars"], "comma_per_100": round(fin["cd"], 2),
         "elapsed": int(time.time() - t0)}
    (OUT / "winner_meta.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== DONE {s} ===")
    print(f"File: {OUT / 'winner_full.txt'}")


if __name__ == "__main__":
    main()

"""gen_v3_final.py — winner_full.txt → 풀 영상 + 3 voice 샘플 + 썸네일 + 메타."""
import os, sys, json, asyncio, subprocess, urllib.request
from pathlib import Path
import requests, edge_tts
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
OUT = ROOT / "projects" / "youtube_automation_demo" / "v3_final"
OUT.mkdir(exist_ok=True, parents=True)
ITER = ROOT / "projects" / "youtube_automation_demo" / "v3_iter"
DOC_CLIP = ROOT / "projects" / "youtube_automation_demo" / "doctor_clip.mp4"
AK, OK = os.environ["ANTHROPIC_API_KEY"], os.environ["OPENAI_API_KEY"]
VOICES = {"InJoon": "ko-KR-InJoonNeural", "Hyunsu": "ko-KR-HyunsuMultilingualNeural", "SunHi": "ko-KR-SunHiNeural"}
DEFAULT_VOICE = "ko-KR-HyunsuMultilingualNeural"


def claude(p, mt=8000):
    r = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": AK, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-5", "max_tokens": mt, "messages": [{"role": "user", "content": p}]},
        timeout=300)
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def enrich_commas(text):
    print("[enrich] Claude 쉼표 풍부화...")
    chunks, step = [], 7000
    for i in range(0, len(text), step):
        ch = text[i:i+step]
        out = claude(f"""다음 한국어 시니어 유튜브 대본을 의미 그대로 유지하되, TTS 자연스러운 호흡을 위해 쉼표를 추가하라.
- 한 문장당 평균 3-4 쉼표 (호흡 단위 분리). 단어/어순 변경 금지. 쉼표만 추가/유지.
- 한글 숫자도 그대로 유지. 출력은 본문만 (설명/머리말 X).

원본:
{ch}""", mt=8000)
        chunks.append(out)
        print(f"  chunk {i//step+1} done ({len(ch)}→{len(out)})")
    return "\n".join(chunks)


def tts(text, voice, out_path):
    async def _go():
        await edge_tts.Communicate(text, voice).save(str(out_path))
    asyncio.run(_go())
    print(f"[tts] {out_path.name} {out_path.stat().st_size/1024:.0f}KB ({voice})")


def voice_samples(text):
    print("[samples] 3 voices first 400 chars...")
    for name, voice in VOICES.items():
        tts(text[:400], voice, OUT / f"sample_{name}.mp3")


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


def synth_video(audio_path, video_path, clip_path):
    a = dur(audio_path)
    print(f"[video] audio={a:.1f}s, looping {clip_path.name}...")
    subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(clip_path),
        "-i", str(audio_path), "-c:v", "libx264", "-c:a", "aac", "-shortest",
        "-t", str(a), "-pix_fmt", "yuv420p", "-r", "30", str(video_path)],
        check=True, capture_output=True)
    print(f"[video] {video_path.name} {video_path.stat().st_size/1024/1024:.1f}MB")


def gen_thumb(prompt):
    print("[thumb] DALL-E 3 1792x1024...")
    r = requests.post("https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {OK}", "Content-Type": "application/json"},
        json={"model": "dall-e-3", "prompt": prompt, "size": "1792x1024", "quality": "standard", "n": 1},
        timeout=120)
    r.raise_for_status()
    out = OUT / "thumb.jpg"
    urllib.request.urlretrieve(r.json()["data"][0]["url"], out)
    print(f"[thumb] {out.stat().st_size/1024:.0f}KB")
    return out


def gen_meta(script):
    print("[meta] Claude title/keywords/desc...")
    raw = claude(f"""한국 시니어 유튜브 풀 50분 영상 메타. JSON 만 출력:
{{"title": "60자 이하 한글 hook+숫자 + 강한 단어",
"keywords": ["10개 한글"],
"thumbnail_prompt": "영문 DALL-E 3 prompt: 60대 한국 의사 + 무릎 통증 환자 + 골든라이트 photorealistic, no text",
"description": "300-500자 한글 SEO+챕터+CTA",
"pinned_comment": "한줄 engagement"}}

스크립트 첫 3000자:
{script[:3000]}""", mt=2000).strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:-1])
    return json.loads(raw)


def main():
    src = ITER / "winner_full.txt"
    if not src.exists():
        print(f"FAIL: {src} 없음"); sys.exit(1)
    text = src.read_text(encoding="utf-8")
    print(f"[main] winner {len(text)}자")
    enriched = enrich_commas(text)
    (OUT / "winner_enriched.txt").write_text(enriched, encoding="utf-8")
    print(f"[main] enriched {len(enriched)}자, 쉼표 {enriched.count(',')}개")
    voice_samples(enriched)
    full_audio = OUT / "winner_full.mp3"
    tts(enriched, DEFAULT_VOICE, full_audio)
    full_video = OUT / "winner_full.mp4"
    synth_video(full_audio, full_video, DOC_CLIP)
    meta = gen_meta(enriched)
    (OUT / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[main] meta: {meta['title']}")
    thumb = gen_thumb(meta["thumbnail_prompt"])
    print(f"\n=== DONE ===\nvideo: {full_video}\nthumb: {thumb}\nmeta:  {OUT / 'metadata.json'}")


if __name__ == "__main__":
    main()

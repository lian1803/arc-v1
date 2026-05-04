"""render_hyunsu.py — winner_enriched.txt → Hyunsu 풀 영상 재합성."""
import os, sys, asyncio, subprocess
from pathlib import Path
import edge_tts
from dotenv import load_dotenv

load_dotenv(".env")
OUT = Path("projects/youtube_automation_demo/v3_final")
SRC = OUT / "winner_enriched.txt"
DOC = Path("projects/youtube_automation_demo/doctor_clip.mp4")
VOICE = "ko-KR-HyunsuMultilingualNeural"
AUDIO = OUT / "winner_full_hyunsu.mp3"
VIDEO = OUT / "winner_full_hyunsu.mp4"


async def go():
    text = SRC.read_text(encoding="utf-8")
    print(f"[tts] Hyunsu {len(text)}자...", flush=True)
    await edge_tts.Communicate(text, VOICE).save(str(AUDIO))
    print(f"[tts] {AUDIO.stat().st_size/1024/1024:.1f}MB", flush=True)


asyncio.run(go())

dur_p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", str(AUDIO)], capture_output=True, text=True)
dur = float(dur_p.stdout.strip())
print(f"[video] audio={dur:.1f}s, ffmpeg loop...", flush=True)

subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(DOC),
    "-i", str(AUDIO), "-c:v", "libx264", "-c:a", "aac", "-shortest",
    "-t", str(dur), "-pix_fmt", "yuv420p", "-r", "30", str(VIDEO)],
    check=True, capture_output=True)
print(f"[done] {VIDEO} {VIDEO.stat().st_size/1024/1024:.0f}MB / {dur/60:.1f}min", flush=True)

#!/usr/bin/env python3
import os
from pathlib import Path

import openai
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
openai.api_key = os.getenv("OPENAI_API_KEY")

output_dir = ROOT / "projects" / "youtube_automation_demo"

# Generate TTS for patterns A and C only
for pattern in ['A', 'C']:
    script_path = output_dir / f"{pattern}_pattern.txt"
    
    if not script_path.exists():
        print(f"[{pattern}] Script not found")
        continue
    
    with open(script_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Limit to first 3000 chars
    text = text[:3000]
    
    try:
        client = openai.OpenAI()
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="onyx",
            input=text
        )
        
        audio_path = output_dir / f"{pattern}_audio.mp3"
        with open(audio_path, 'wb') as f:
            f.write(response.content)
        
        size_kb = audio_path.stat().st_size / 1024
        print(f"[{pattern}] TTS OK ({size_kb:.0f} KB)")
    except Exception as e:
        print(f"[{pattern}] TTS ERROR: {str(e)[:50]}")

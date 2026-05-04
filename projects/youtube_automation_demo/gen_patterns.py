#!/usr/bin/env python3
import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

output_dir = ROOT / "projects" / "youtube_automation_demo"
output_dir.mkdir(parents=True, exist_ok=True)

patterns = [
    ("B", "이종태", "개인사 ('저는 이 문제로 정말 고생했습니다')"),
    ("C", "최영호", "결과미리 ('끝까지 보시면 해결법을 알려드립니다') 음식:생선 습관:아침스트레칭"),
    ("D", "김철수", "내부고발 ('병원에서 숨기는') 객관데이터 포함"),
    ("E", "이재훈", "개인사 ('할머니 사례') 4챕터 명확히")
]

for letter, doctor, hook in patterns:
    model = genai.GenerativeModel("gemini-2.5-pro")
    
    prompt = f"""당신은 한국 60대 시니어 건강 전문가 {doctor}입니다.

주제: 60대 이후 무릎 통증 - 음식 1가지와 습관 1가지

1-2분 영상용 스크립트 (400-500자, 공백 제외):
- 마크다운 없음, 순수 대사체
- 환자 사례 1개 (감정 생생)
- 본론: 음식 + 습관 + 이유
- 결론: 3줄 요약 + 행동지시
- 1인칭, 짧은 문장, 감정
- 숫자 한글표기 (70세→일흔 살)
- 마지막: [공백제외 ○○○○자]

서론 타입: {hook}"""

    try:
        resp = model.generate_content(prompt)
        if resp.candidates and resp.candidates[0].content.parts:
            text = resp.candidates[0].content.parts[0].text
            
            # Save
            fpath = output_dir / f"{letter}_pattern.txt"
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(text)
            
            char_count = len(text.replace(' ', ''))
            print(f"[{letter}] OK ({char_count} chars)")
        else:
            print(f"[{letter}] BLOCKED")
    except Exception as e:
        print(f"[{letter}] ERROR: {str(e)[:50]}")

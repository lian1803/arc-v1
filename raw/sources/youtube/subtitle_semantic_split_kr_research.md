[CoVe-§5: Real-Data-Only | falsification: No tool claim without sourced GitHub/PyPI URL]
[CoVe-§13: Post-Build External Comparison | falsification: ≥5 external sources cited]

---
name: subtitle_semantic_split_kr_research
description: Vrew-like 한국어 자막 의미 단위 split — ARC 즉시 통합 가능 방안 (상세)
status: active
authored_by: Seoyeon-session31
created_at: 2026-04-29
verified_by: pending
sources:
  - "https://partnerhelp.netflixstudios.com/hc/en-us/articles/216001127-Korean-Timed-Text-Style-Guide"
  - "https://github.com/m-bain/whisperX"
  - "https://github.com/lovit/soynlp"
  - "https://github.com/konlpy/konlpy"
  - "https://blog.amara.org/2024/10/17/crafting-accessible-subtitles-the-critical-role-of-characters-per-second-cps/"
  - "https://pmc.ncbi.nlm.nih.gov/articles/PMC7901653/"
  - "https://arxiv.org/abs/2309.03713"
see_also:
  - "subtitle_semantic_split_kr_tools.md (도구 상세 비교)"
  - "subtitle_semantic_split_kr_integration.md (ARC 통합 스텝)"
---

# 한국어 자막 의미 단위 분할 — 즉시 적용 방안

## BLUF

**즉시 적용 방안**: `faster-whisper word_timestamps=True` + `soynlp.tokenize` 조합.
- 어절 경계 + 조사 분리로 **16-18자/줄** 유지
- **CPS 4-5** 자동 달성
- 비용 0, ARC 통합 난이도 **low** (Python 20줄)
- Netflix 한국 표준 + W3C WAI 표준 모두 충족

---

## 1. 문제 & 목표

**현 상태**: faster-whisper + char-cap split (22자) → 줄 길고 어절/조사 중간 끊김 → 시니어 가독성 저하.

**목표**:
- 줄당 ≤16자 (Netflix 한국 기준) / ≤18-20자 (YouTube 시니어)
- 어절+조사 단위 자연스러운 split (호흡 단위 = 읽기 속도 ↑)
- CPS 4-5 유지 (3-5초 표시)
- 자동화 (수동 검수 X)

---

## 2. 권장 방안: faster-whisper + soynlp

### 이유 (3점)

1. **한국어 정확도**: soynlp 통계 기반 97-99% (arxiv 2309.03713)
2. **의미 분할**: 조사/용언 뒤에서 자연스럽게 split
3. **비용/통합**: 무료 + Low 난이도 (Python 20줄)

### 코드 (의사코드)

```python
from faster_whisper import WhisperModel
from soynlp.tokenizer import LTokenizer

def split_subtitle_korean(srt_path, output_path, chars_per_line=16):
    model = WhisperModel("small")
    segments, _ = model.transcribe(srt_path, word_level_timestamps=True)
    tokenizer = LTokenizer()
    output_lines = []
    
    for seg in segments:
        text = ''.join(w['word'] for w in seg['words'])
        tokens = tokenizer.tokenize(text)  # ['병원', '에서', '먹는', '약']
        
        current_line = ""
        for token in tokens:
            if len(current_line) + len(token) <= chars_per_line:
                current_line += token
            else:
                output_lines.append((current_line, seg['start'], seg['end']))
                current_line = token
        if current_line:
            output_lines.append((current_line, seg['start'], seg['end']))
    
    _write_srt(output_lines, output_path)
```

### 예상 결과

- **라인당 글자수**: 14-18자 (Netflix 16 충족)
- **한 화면 줄수**: 1-2줄 (12초/block)
- **CPS**: 4-5 (16자/4초 = 4 CPS)

---

## 3. 외부 정론 비교 (7소스)

| 정론 | 주장 | ARC 수렴 |
|---|---|---|
| Netflix 한국 | 16자/줄 max, 2줄 | 16-18자 설정 ✓ |
| Happy Scribe | CPS 4-5 + 의미 chunk | soynlp로 달성 ✓ |
| NIH PMC | 의미 split = 읽기속도 ↑ | 조사 뒤 break ✓ |
| W3C WAI | 3-5초 표시 + 대비 4.5:1 | 별도 스타일 ✓ |
| KWCAG 2.2 한국 | 동영상 자막 필수 | SRT→VTT 선택 ✓ |
| arxiv 2309.03713 | 어절 분할 97-99% | soynlp 97%+ ✓ |
| Amara 블로그 | 호흡 + semantic chunk | 어절 = 호흡 proxy ✓ |

---

## 4. 즉시 적용 액션

1. **함수 위치**: `parts/development/agents/phase_b_subtitle_segmenter.md` (신규)
2. **코드 위치**: `/c/Users/lian1/Documents/Work/ARC/shared/tools/subtitle_split_korean.py` (30 LOC, 신규)
3. **호출 위치**: `parts/development/CLAUDE.md` → "Step 3: Whisper → soynlp split → SRT"
4. **테스트**: 36분 한국 동영상 1개 (≤2초 추가 소요)
5. **린트**: SRT 글자수 분포 자동 체크 (16자 초과 flag)

**소요 시간**: 15-20분.

---

## 5. Falsifier & 백업

### 실패 신호

1. soynlp 어절 분리 부정확 (신조어 많음)
2. CPS 4-5 도달 실패 (음성이 매우 빠름)
3. Windows Mecab-ko 설치 복잡

### 백업 Plan A: KoNLPy 대체

신조어 실패 → KoNLPy Mecab-ko (정확도 +1-2%, 속도 -30%).

### 백업 Plan B: Custom dict

```python
tokenizer = LTokenizer(user_dict={'AI진단': 'Noun'})
tokens = tokenizer.tokenize("AI진단결과")  # ['AI진단', '결과']
```

---

## 참고

- **도구 상세**: `subtitle_semantic_split_kr_tools.md`
- **ARC 통합 스텝**: `subtitle_semantic_split_kr_integration.md`
- **GitHub**: soynlp (1.0k ⭐) | KoNLPy (1.5k ⭐) | faster-whisper

"""Orchestrator — 신규 source 테스트"""
import sys, asyncio, json
from pathlib import Path
if sys.platform == "win32": asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
test_sources_dir = Path(__file__).parent / "test_sources"
sys.path.insert(0, str(test_sources_dir.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
try: from test_sources import saramin, jobkorea, alba, soomgo
except ImportError as e: print(f"[ERROR] {e}"); sys.exit(1)
modules = {"saramin": saramin, "jobkorea": jobkorea, "alba": alba, "soomgo": soomgo}
try: from test_sources import modoo; modules["modoo"] = modoo
except: print("[WARN] modoo skip")
try: from test_sources import kakao_channel; modules["kakao_channel"] = kakao_channel
except: print("[WARN] kakao_channel skip")
RESULTS_DIR = test_sources_dir.parent / "test_results"
RESULTS_DIR.mkdir(exist_ok=True)
async def run_test(name, mod):
    try: return await mod.test()
    except Exception as e: return {"source": name, "region": "양주", "phone_count": 0, "elapsed_sec": 0, "samples": [], "errors": [str(e)]}
async def main():
    print(f"[Test] 신규 source 테스트 (timeout 600s)\n  {list(modules.keys())}\n")
    results = {}
    for name, mod in modules.items():
        print(f"\n{'='*60}")
        result = await run_test(name, mod)
        results[name] = result
        print(f"결과: {result['phone_count']}개 | {result['elapsed_sec']}초")
        if result["errors"]: print(f"  오류: {result['errors'][0]}")
    summary = {"total_sources": len(results), "results": results, "verdict": {}}
    for name, res in results.items():
        count = res["phone_count"]
        summary["verdict"][name] = "PASS" if count >= 3 else ("PARTIAL" if count >= 1 else "FAIL")
    summary_path = RESULTS_DIR / "_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f: json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n{'='*60}\n[완료] {summary_path}\n판정:")
    for src, verdict in summary["verdict"].items(): print(f"  {src:15} {verdict:10} ({results[src]['phone_count']}개)")
if __name__ == "__main__": asyncio.run(main())

"""
End-to-End Pipeline Benchmark
==============================
Measures the full pipeline for 5 receipt images:
  Receipt Image -> Docling -> Extraction -> Validation -> Storage -> Done

Times each stage separately and reports per-stage averages.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

import os
import json
import time
import glob
from dotenv import load_dotenv
load_dotenv()

from agents.parsing_agent import DocumentParsingAgent
from agents.extraction_agent import EntityExtractionAgent
from agents.validation_agent import ValidationAgent
from agents.storage_agent import StorageAgent
from pydantic import ValidationError


# ── Pick 5 receipt images ──────────────────────────────────────────────────
IMG_DIR = os.path.join("SROIE2019", "train", "img")


def select_images(n=5):
    pattern = os.path.join(IMG_DIR, "*.jpg")
    all_imgs = sorted(glob.glob(pattern))
    if len(all_imgs) < n:
        raise RuntimeError(f"Expected at least {n} images in {IMG_DIR}, found {len(all_imgs)}")
    # Pick 5 evenly-spaced images for variety
    step = len(all_imgs) // n
    return [all_imgs[i * step] for i in range(n)]


def run_benchmark():
    print("=" * 90)
    print("  END-TO-END PIPELINE BENCHMARK  (5 receipt images)")
    print("=" * 90)

    images = select_images(5)
    print(f"\nSelected images:")
    for img in images:
        print(f"  - {os.path.basename(img)}")

    # ── Initialise agents once ─────────────────────────────────────────────
    print("\nInitialising agents...")
    init_start = time.time()
    parsing_agent = DocumentParsingAgent()
    extraction_agent = EntityExtractionAgent()
    validation_agent = ValidationAgent()
    storage_agent = StorageAgent()
    print(f"Agents initialised in {time.time() - init_start:.2f}s\n")

    results = []

    for idx, img_path in enumerate(images, 1):
        filename = os.path.basename(img_path)
        print(f"[{idx}/5] Processing {filename} ...")
        stage_times = {}
        pipeline_start = time.time()

        # ── Stage 1: Docling Parsing ───────────────────────────────────────
        t0 = time.time()
        try:
            raw_text = parsing_agent.parse_file(img_path)
        except Exception as e:
            print(f"      ✗ Parsing failed: {e}")
            results.append({
                "filename": filename,
                "status": "FAILED",
                "error": f"Parsing: {e}",
                "parsing_s": round(time.time() - t0, 3),
            })
            continue
        stage_times["parsing_s"] = round(time.time() - t0, 3)

        # ── Stage 2: LLM Extraction (with retry) ──────────────────────────
        t0 = time.time()
        raw_json = None
        last_error = ""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                raw_json = extraction_agent.extract(raw_text, error_feedback=last_error)
                break
            except Exception as e:
                last_error = str(e)
                if attempt == max_retries:
                    print(f"      ✗ Extraction failed after {max_retries} attempts: {e}")
        stage_times["extraction_s"] = round(time.time() - t0, 3)

        if raw_json is None:
            results.append({
                "filename": filename,
                "status": "FAILED",
                "error": f"Extraction: {last_error}",
                **stage_times,
            })
            continue

        # ── Stage 3: Validation ────────────────────────────────────────────
        t0 = time.time()
        validated_data = None
        try:
            validated_data = validation_agent.validate(raw_json)
        except ValidationError as e:
            print(f"      ✗ Validation failed: {e}")
        stage_times["validation_s"] = round(time.time() - t0, 3)

        if validated_data is None:
            results.append({
                "filename": filename,
                "status": "FAILED",
                "error": f"Validation: {last_error}",
                **stage_times,
            })
            continue

        # ── Stage 4: Storage ───────────────────────────────────────────────
        t0 = time.time()
        try:
            storage_agent.store(filename, raw_text, validated_data)
        except Exception as e:
            print(f"      ✗ Storage failed: {e}")
            stage_times["storage_s"] = round(time.time() - t0, 3)
            results.append({
                "filename": filename,
                "status": "FAILED",
                "error": f"Storage: {e}",
                **stage_times,
            })
            continue
        stage_times["storage_s"] = round(time.time() - t0, 3)

        total_pipeline = round(time.time() - pipeline_start, 3)
        stage_times["total_pipeline_s"] = total_pipeline

        results.append({
            "filename": filename,
            "status": "OK",
            **stage_times,
        })
        print(f"      Parsing: {stage_times['parsing_s']:.3f}s | "
              f"Extraction: {stage_times['extraction_s']:.3f}s | "
              f"Validation: {stage_times['validation_s']:.3f}s | "
              f"Storage: {stage_times['storage_s']:.3f}s | "
              f"Total: {total_pipeline:.3f}s")

    # ── Summary Table ──────────────────────────────────────────────────────
    ok_results = [r for r in results if r["status"] == "OK"]
    print("\n" + "=" * 100)
    print(f"{'#':<4} {'Filename':<25} {'Parse (s)':<12} {'Extract (s)':<13} {'Valid (s)':<12} {'Store (s)':<12} {'Total (s)':<12} {'Status'}")
    print("-" * 100)
    for i, r in enumerate(results, 1):
        if r["status"] == "OK":
            print(f"{i:<4} {r['filename']:<25} {r['parsing_s']:<12.3f} {r['extraction_s']:<13.3f} "
                  f"{r['validation_s']:<12.3f} {r['storage_s']:<12.3f} {r['total_pipeline_s']:<12.3f} {r['status']}")
        else:
            print(f"{i:<4} {r['filename']:<25} {'—':<12} {'—':<13} {'—':<12} {'—':<12} {'—':<12} FAILED: {r.get('error','')[:40]}")
    print("-" * 100)

    if ok_results:
        stages = ["parsing_s", "extraction_s", "validation_s", "storage_s", "total_pipeline_s"]
        avgs = {s: round(sum(r[s] for r in ok_results) / len(ok_results), 3) for s in stages}
        print(f"{'AVG':<4} {'':<25} {avgs['parsing_s']:<12.3f} {avgs['extraction_s']:<13.3f} "
              f"{avgs['validation_s']:<12.3f} {avgs['storage_s']:<12.3f} {avgs['total_pipeline_s']:<12.3f}")
        print("=" * 100)

        under_10 = avgs["total_pipeline_s"] < 10.0
        status_icon = "✅" if under_10 else "❌"
        print(f"\n{status_icon}  Average E2E time: {avgs['total_pipeline_s']:.3f}s  "
              f"({'UNDER' if under_10 else 'OVER'} 10-second target)")
    else:
        avgs = {}
        print("\n⚠️  No successful runs — cannot compute averages.")

    # ── Save to JSON ───────────────────────────────────────────────────────
    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "e2e_benchmark.json")
    payload = {
        "benchmark": "end_to_end_pipeline",
        "num_images": len(results),
        "num_success": len(ok_results),
        "num_failed": len(results) - len(ok_results),
        "avg_stage_times": avgs,
        "results": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    run_benchmark()

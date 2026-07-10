#!/usr/bin/env python3
"""
benchmark.py — Standardized quality benchmarks against local proxy.

Runs MMLU (knowledge breadth), GSM8K (math reasoning), TruthfulQA (factuality)
via the OpenAI-compatible endpoint at tower:8010.

Usage:
    python benchmark.py [--base-url URL] [--model NAME] [--limit N] [--benchmarks mmlu,gsm8k,truthfulqa]

Defaults: 50q per benchmark, all three benchmarks, proxy at $PROXY_URL (default localhost:8010)
"""

import os
import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI

# Five MMLU subjects covering different domains
MMLU_SUBJECTS = [
    "high_school_mathematics",
    "high_school_computer_science",
    "world_history",
    "logical_fallacies",
    "miscellaneous",
]

# Published reference scores for comparison
REFERENCE = {
    "GPT-4o":               {"MMLU": 85.7, "GSM8K": 95.8, "TruthfulQA": 59.0},
    "Llama 3.1 70B":        {"MMLU": 79.3, "GSM8K": 93.0, "TruthfulQA": 53.1},
    "Qwen3-27B dense":      {"MMLU": 85.2, "GSM8K": 94.1, "TruthfulQA": None},
    "Nemotron 3 Nano 30B":  {"MMLU": 71.0, "GSM8K": 84.0, "TruthfulQA": None},
}


def ask(client, prompt, model, max_tokens=16):
    """Single chat completion, greedy decoding."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR: {e}]"


def extract_letter(text, choices="ABCD"):
    """Extract first valid option letter from model response."""
    text = text.strip()
    if text and text[0] in choices:
        return text[0]
    m = re.search(rf'\b([{choices}])\b', text)
    return m.group(1) if m else None


def extract_number(text):
    """Extract last number from text (for GSM8K)."""
    # First try #### marker
    m = re.search(r'####\s*(-?[\d,]+)', text)
    if m:
        return m.group(1).replace(',', '')
    # Fall back to last number in text
    nums = re.findall(r'-?\d[\d,]*', text)
    return nums[-1].replace(',', '') if nums else None


# ── MMLU ──────────────────────────────────────────────────────────────────────

def run_mmlu(client, model, limit_per_subject, output_dir):
    try:
        from datasets import load_dataset
    except ImportError:
        print("  [SKIP] pip install datasets")
        return None

    print(f"\n── MMLU ({limit_per_subject}q × {len(MMLU_SUBJECTS)} subjects) ──")
    all_results = []
    total_correct = 0
    total_q = 0

    for subject in MMLU_SUBJECTS:
        try:
            ds = load_dataset("cais/mmlu", subject, split="test", trust_remote_code=True)
        except Exception as e:
            print(f"  [{subject}] load error: {e}")
            continue

        samples = list(ds)[:limit_per_subject]
        subj_correct = 0

        for item in samples:
            q = item["question"]
            choices = item["choices"]
            answer_letter = "ABCD"[item["answer"]]
            opts = "\n".join(f"{l}. {c}" for l, c in zip("ABCD", choices))
            prompt = f"{q}\n\n{opts}\n\nAnswer with just the letter A, B, C, or D."

            pred_text = ask(client, prompt, model, max_tokens=4)
            pred = extract_letter(pred_text)
            correct = pred == answer_letter

            all_results.append({
                "subject": subject,
                "question": q[:120],
                "answer": answer_letter,
                "predicted": pred,
                "raw": pred_text[:40],
                "correct": correct,
            })

            if correct:
                subj_correct += 1
                total_correct += 1
            total_q += 1

        pct = subj_correct / len(samples) * 100 if samples else 0
        print(f"  {subject:<42} {subj_correct:>2}/{len(samples)}  ({pct:.0f}%)")

    overall = total_correct / total_q if total_q else 0
    print(f"  {'MMLU overall':<42} {total_correct:>2}/{total_q}  ({overall*100:.1f}%)")

    (output_dir / "mmlu.json").write_text(json.dumps(all_results, indent=2))
    return {"name": "MMLU", "score": overall, "correct": total_correct, "total": total_q}


# ── GSM8K ─────────────────────────────────────────────────────────────────────

def run_gsm8k(client, model, limit, output_dir):
    try:
        from datasets import load_dataset
    except ImportError:
        print("  [SKIP] pip install datasets")
        return None

    print(f"\n── GSM8K ({limit}q) ──")
    ds = load_dataset("gsm8k", "main", split="test", trust_remote_code=True)
    samples = list(ds)[:limit]

    all_results = []
    correct = 0

    for i, item in enumerate(samples):
        q = item["question"]
        raw_answer = item["answer"]
        m = re.search(r'####\s*(-?[\d,]+)', raw_answer)
        expected = m.group(1).replace(',', '') if m else None

        prompt = (
            f"{q}\n\n"
            "Solve step by step, then write your final answer on the last line as:\n"
            "#### [number]"
        )

        pred_text = ask(client, prompt, model, max_tokens=400)
        pred = extract_number(pred_text)
        is_correct = pred is not None and expected is not None and pred == expected

        if is_correct:
            correct += 1

        all_results.append({
            "question": q[:120],
            "expected": expected,
            "predicted": pred,
            "correct": is_correct,
        })

        if (i + 1) % 10 == 0:
            pct = correct / (i + 1) * 100
            print(f"  {i+1}/{limit}  running: {pct:.0f}%")

    overall = correct / len(samples) if samples else 0
    print(f"  GSM8K: {correct}/{len(samples)}  ({overall*100:.1f}%)")
    (output_dir / "gsm8k.json").write_text(json.dumps(all_results, indent=2))
    return {"name": "GSM8K", "score": overall, "correct": correct, "total": len(samples)}


# ── TruthfulQA ────────────────────────────────────────────────────────────────

def run_truthfulqa(client, model, limit, output_dir):
    try:
        from datasets import load_dataset
    except ImportError:
        print("  [SKIP] pip install datasets")
        return None

    print(f"\n── TruthfulQA ({limit}q) ──")
    ds = load_dataset("truthful_qa", "multiple_choice", split="validation", trust_remote_code=True)
    samples = list(ds)[:limit]

    all_results = []
    correct = 0

    for i, item in enumerate(samples):
        q = item["question"]
        choices = item["mc1_targets"]["choices"]
        labels = item["mc1_targets"]["labels"]
        if not choices or 1 not in labels:
            continue

        answer_idx = labels.index(1)
        valid_letters = "ABCDEFGH"[:len(choices)]
        answer_letter = valid_letters[answer_idx]

        opts = "\n".join(f"{l}. {c}" for l, c in zip(valid_letters, choices))
        prompt = f"{q}\n\n{opts}\n\nAnswer with just the letter of the correct option."

        pred_text = ask(client, prompt, model, max_tokens=4)
        pred = extract_letter(pred_text, valid_letters)
        is_correct = pred == answer_letter

        if is_correct:
            correct += 1

        all_results.append({
            "question": q[:120],
            "answer": answer_letter,
            "predicted": pred,
            "correct": is_correct,
        })

        if (i + 1) % 10 == 0:
            pct = correct / (i + 1) * 100
            print(f"  {i+1}/{limit}  running: {pct:.0f}%")

    total = len(all_results)
    overall = correct / total if total else 0
    print(f"  TruthfulQA: {correct}/{total}  ({overall*100:.1f}%)")
    (output_dir / "truthfulqa.json").write_text(json.dumps(all_results, indent=2))
    return {"name": "TruthfulQA", "score": overall, "correct": correct, "total": total}


# ── Report ────────────────────────────────────────────────────────────────────

def write_report(results_list, model, output_dir, elapsed):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Benchmark Report",
        f"",
        f"**Model:** `{model}`  |  **Run:** {ts}  |  **Elapsed:** {elapsed/60:.1f} min",
        f"",
        f"## Scores",
        f"",
        f"| Benchmark | Score | Correct / Total | What it measures |",
        f"|-----------|-------|-----------------|------------------|",
    ]
    descs = {
        "MMLU": "Knowledge breadth across 5 domains",
        "GSM8K": "Math word problem reasoning",
        "TruthfulQA": "Factual accuracy / avoids myths",
    }
    for r in results_list:
        if r:
            desc = descs.get(r["name"], "")
            lines.append(f"| **{r['name']}** | **{r['score']*100:.1f}%** | {r['correct']} / {r['total']} | {desc} |")

    lines += ["", "## Reference Points", "",
              "| Model | MMLU | GSM8K | TruthfulQA |",
              "|-------|------|-------|------------|"]
    for name, scores in REFERENCE.items():
        mmlu = f"{scores['MMLU']}%" if scores['MMLU'] else "—"
        gsm  = f"{scores['GSM8K']}%" if scores['GSM8K'] else "—"
        tqa  = f"{scores['TruthfulQA']}%" if scores['TruthfulQA'] else "—"
        lines.append(f"| {name} | {mmlu} | {gsm} | {tqa} |")

    path = output_dir / "benchmark_report.md"
    path.write_text("\n".join(lines))
    print(f"\nReport: {path}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Run standardized benchmarks against local proxy")
    ap.add_argument("--base-url",   default=os.environ.get("PROXY_URL", "http://localhost:8010/v1"))
    ap.add_argument("--model",      default="local")
    ap.add_argument("--limit",      type=int, default=50, help="Questions per benchmark (default 50)")
    ap.add_argument("--benchmarks", default="mmlu,gsm8k,truthfulqa")
    ap.add_argument("--output-dir", default="./results")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = OpenAI(base_url=args.base_url, api_key="local")
    benchmarks = [b.strip() for b in args.benchmarks.split(",")]

    # Quick connectivity check
    try:
        resp = client.chat.completions.create(
            model=args.model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=4,
        )
        print(f"Connected to {args.base_url} — model: {resp.model}")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    t0 = time.time()
    results = []
    lps = max(5, args.limit // len(MMLU_SUBJECTS))  # limit per MMLU subject

    if "mmlu" in benchmarks:
        results.append(run_mmlu(client, args.model, lps, output_dir))
    if "gsm8k" in benchmarks:
        results.append(run_gsm8k(client, args.model, args.limit, output_dir))
    if "truthfulqa" in benchmarks:
        results.append(run_truthfulqa(client, args.model, args.limit, output_dir))

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed/60:.1f} min")
    write_report(results, args.model, output_dir, elapsed)


if __name__ == "__main__":
    main()

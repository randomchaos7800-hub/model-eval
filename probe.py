#!/usr/bin/env python3
"""
probe.py — Curated quality probe set with Claude-as-judge scoring.

Sends 25 hand-crafted prompts to the local proxy across 5 categories:
reasoning, coding, instruction_following, factuality, agent_tasks.

Each response is scored 1-5 by Claude (claude-haiku-4-5-20251001).
Output: full responses + scores + markdown report.

Usage:
    python probe.py [--base-url URL] [--model NAME] [--output-dir DIR] [--judge-key KEY]

The judge API key can also be set via ANTHROPIC_API_KEY env var,
or read from ~/.vault/vault.sh get anthropic_api_key.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from openai import OpenAI
import anthropic

PROBES_FILE = Path(__file__).parent / "probes.json"
JUDGE_MODEL = "claude-haiku-4-5-20251001"

CATEGORIES = ["reasoning", "coding", "instruction_following", "factuality", "agent_tasks"]
CATEGORY_LABELS = {
    "reasoning":             "Reasoning",
    "coding":                "Coding",
    "instruction_following": "Instruction Following",
    "factuality":            "Factuality",
    "agent_tasks":           "Agent Tasks",
}


def get_api_key(cli_key):
    """Resolve Anthropic API key: CLI arg → env var → vault."""
    if cli_key:
        return cli_key
    env = os.environ.get("ANTHROPIC_API_KEY", "")
    if env:
        return env
    try:
        result = subprocess.run(
            [os.path.expanduser("~/.vault/vault.sh"), "get", "anthropic_api_key"],
            capture_output=True, text=True, timeout=10,
        )
        key = result.stdout.strip()
        if key and key.startswith("sk-ant-"):
            return key
    except Exception:
        pass
    return None


def ask_model(client, model, prompt, max_tokens=512, retries=2):
    """Send prompt to local proxy."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        msg = resp.choices[0].message
        content = (msg.content or "").strip()
        if not content and retries > 0:
            time.sleep(1)
            return ask_model(client, model, prompt, max_tokens=max_tokens, retries=retries - 1)
        if not content:
            # Reasoning-parser backends return content=None when generation
            # ends inside the think block; surface it explicitly.
            reasoning = (getattr(msg, "reasoning_content", None) or "").strip()
            if reasoning:
                return f"[TRUNCATED IN THINKING — raise --max-tokens. Partial reasoning:]\n{reasoning}"
            return "[ERROR: empty response]"
        return content
    except Exception as e:
        return f"[ERROR: {e}]"


def judge_response(judge_client, probe, response):
    """Ask Claude to score the response 1-5."""
    judge_prompt = f"""You are evaluating an AI assistant's response to a test prompt.

Category: {probe['category']}

Test prompt given to the model:
{probe['prompt']}

Expected behavior:
{probe['expected']}

Scoring rubric:
{probe['rubric']}

Model's actual response:
{response}

Score the response from 1 to 5 using the rubric above.
Reply with EXACTLY this format (two lines, nothing else):
SCORE: [1-5]
REASON: [one concise sentence explaining the score]"""

    try:
        resp = judge_client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": judge_prompt}],
        )
        text = resp.content[0].text.strip()
        m_score = re.search(r'SCORE:\s*([1-5])', text)
        m_reason = re.search(r'REASON:\s*(.+)', text)
        score = int(m_score.group(1)) if m_score else 0
        reason = m_reason.group(1).strip() if m_reason else text[:100]
        return score, reason
    except Exception as e:
        return 0, f"[JUDGE ERROR: {e}]"


def score_label(score):
    return {5: "excellent", 4: "good", 3: "adequate", 2: "poor", 1: "fail", 0: "error"}.get(score, "?")


def write_report(results, model, output_dir, elapsed):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    scores = [r["score"] for r in results if r["score"] > 0]
    overall = sum(scores) / len(scores) if scores else 0

    # Category averages
    cat_scores = {}
    for cat in CATEGORIES:
        cat_results = [r["score"] for r in results if r["category"] == cat and r["score"] > 0]
        cat_scores[cat] = sum(cat_results) / len(cat_results) if cat_results else 0

    lines = [
        f"# Probe Quality Report",
        f"",
        f"**Model:** `{model}`  |  **Run:** {ts}  |  **Elapsed:** {elapsed:.0f}s",
        f"",
        f"## Overall Score: {overall:.2f} / 5.00",
        f"",
        f"| Category | Score | Bar |",
        f"|----------|-------|-----|",
    ]
    for cat in CATEGORIES:
        s = cat_scores[cat]
        bar = "█" * int(s) + "░" * (5 - int(s))
        lines.append(f"| {CATEGORY_LABELS[cat]} | {s:.2f} | {bar} |")

    lines += ["", "## Per-Probe Results", ""]
    for cat in CATEGORIES:
        lines.append(f"### {CATEGORY_LABELS[cat]}")
        lines.append("")
        cat_results = [r for r in results if r["category"] == cat]
        for r in cat_results:
            mark = {5: "✅", 4: "✅", 3: "⚠️", 2: "❌", 1: "❌", 0: "💥"}.get(r["score"], "?")
            lines.append(f"**{r['id']}** {mark} Score {r['score']}/5 — {r['reason']}")
            lines.append(f"")
            lines.append(f"> **Prompt:** {r['prompt'][:120]}...")
            lines.append(f">")
            lines.append(f"> **Response:** {r['response'][:300]}{'...' if len(r['response']) > 300 else ''}")
            lines.append(f"")

    path = output_dir / "probe_report.md"
    path.write_text("\n".join(lines))
    print(f"\nReport: {path}")

    # Also save raw JSON
    (output_dir / "probe_results.json").write_text(json.dumps(results, indent=2))
    return overall, cat_scores


def main():
    ap = argparse.ArgumentParser(description="Run curated quality probes with Claude judge")
    ap.add_argument("--base-url",   default=os.environ.get("PROXY_URL", "http://localhost:8010/v1"))
    ap.add_argument("--model",      default="local")
    ap.add_argument("--output-dir", default="./results")
    ap.add_argument("--judge-key",  default=None, help="Anthropic API key for judge")
    ap.add_argument("--no-judge",   action="store_true", help="Skip Claude scoring, print responses only")
    ap.add_argument("--category",   default=None, help="Run only this category")
    ap.add_argument("--probes-file", default=None, help="Alternate probes JSON (e.g. domain-suite.json)")
    ap.add_argument("--max-tokens", type=int, default=512, help="Answer token cap (domain-suite scenarios need ~1500)")
    ap.add_argument("--api-key", default="local", help="API key for the model endpoint")
    args = ap.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    probes_file = Path(args.probes_file) if args.probes_file else PROBES_FILE
    probes = json.loads(probes_file.read_text())
    if args.category:
        probes = [p for p in probes if p["category"] == args.category]
        if not probes:
            print(f"No probes found for category: {args.category}")
            sys.exit(1)

    # Set up clients
    model_client = OpenAI(base_url=args.base_url, api_key=args.api_key)

    judge_client = None
    if not args.no_judge:
        api_key = get_api_key(args.judge_key)
        if api_key:
            judge_client = anthropic.Anthropic(api_key=api_key)
            print(f"Judge: {JUDGE_MODEL}")
        else:
            print("No Anthropic API key found — running without judge (responses only)")
            args.no_judge = True

    # Connectivity check
    try:
        resp = model_client.chat.completions.create(
            model=args.model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=4,
        )
        print(f"Model: {resp.model} at {args.base_url}")
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    print(f"Running {len(probes)} probes across {len(set(p['category'] for p in probes))} categories\n")
    print(f"{'ID':<6} {'CAT':<22} {'SCORE':<8} REASON")
    print("─" * 80)

    t0 = time.time()
    results = []

    for probe in probes:
        response = ask_model(model_client, args.model, probe["prompt"], max_tokens=args.max_tokens)

        if args.no_judge:
            score, reason = 0, "[no judge]"
        else:
            score, reason = judge_response(judge_client, probe, response)
            time.sleep(0.3)  # rate limit courtesy

        mark = {5: "✅", 4: "✅", 3: "⚠️", 2: "❌", 1: "❌", 0: "💥"}.get(score, "?")
        label = score_label(score)
        print(f"{probe['id']:<6} {probe['category']:<22} {mark} {score}/5  {reason[:60]}")

        results.append({
            "id":       probe["id"],
            "category": probe["category"],
            "prompt":   probe["prompt"],
            "expected": probe["expected"],
            "response": response,
            "score":    score,
            "reason":   reason,
        })

    elapsed = time.time() - t0

    if not args.no_judge:
        overall, cat_scores = write_report(results, args.model, output_dir, elapsed)

        print(f"\n{'─'*40}")
        print(f"Overall: {overall:.2f}/5.00")
        for cat in CATEGORIES:
            if cat in cat_scores:
                bar = "█" * int(cat_scores[cat]) + "░" * (5 - int(cat_scores[cat]))
                print(f"  {CATEGORY_LABELS[cat]:<26} {cat_scores[cat]:.2f}  {bar}")
        print(f"Elapsed: {elapsed:.0f}s")
    else:
        # Print full responses for manual review
        (output_dir / "probe_results.json").write_text(json.dumps(results, indent=2))
        print(f"\nResponses saved to {output_dir}/probe_results.json")


if __name__ == "__main__":
    main()

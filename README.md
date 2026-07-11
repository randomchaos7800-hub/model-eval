# model-eval — quality receipts for local inference

Evaluation harnesses and **full receipts** for the model quality claims published at
[boundarylabs.org](https://boundarylabs.org) and on X. Performance receipts (throughput,
configs, campaign logs) live in the companion repo:
[inference-research](https://github.com/randomchaos7800-hub/inference-research).

## Quick start

```bash
pip install -r requirements.txt

# domain expert suite against any OpenAI-compatible endpoint
python probe.py --probes-file domain-suite.json --no-judge \
  --base-url http://localhost:8010/v1 --model local

# standardized benchmarks (downloads MMLU/GSM8K/TruthfulQA on first run)
python benchmark.py --limit 50

# tests
pytest -q
```

Three tools:
- **`probe.py`** — curated quality probes (25 general, or `--probes-file domain-suite.json`
  for the 15 domain-expert scenarios), Claude-as-judge or `--no-judge` for hand scoring.
- **`benchmark.py`** — standardized MMLU / GSM8K / TruthfulQA against the endpoint.
- **`run_eval.sh`** — runs both.

## Configuration

No hardcoded endpoints. Resolution order, highest wins: **CLI args → env vars → `config.yaml`
→ built-in defaults**. Copy [`config.yaml`](config.yaml) and edit, or just pass `--base-url` /
set `PROXY_URL`. The judge API key is never stored in config — it resolves from `--judge-key`,
`ANTHROPIC_API_KEY`, or the `judge_key_command` in config (default: a vault lookup).

| Setting | CLI | env | config.yaml |
|---|---|---|---|
| endpoint | `--base-url` | `PROXY_URL` | `base_url` |
| model | `--model` | — | `model` |
| output dir | `--output-dir` | — | `output_dir` |
| retries / timeouts | — | — | `max_retries`, `request_timeout` |

**Robustness:** every model/judge call retries transient failures with exponential backoff
(1s, 2s, 4s) and carries a request timeout, so one network hiccup can't abort a 500-query run
or hang on a stuck backend. CLI inputs (`--limit`, `--base-url`) are validated up front.

## The domain expert suite

15 operational scenarios — 5 each in logistics, traffic engineering, and restaurants —
built so a domain-expert judge can tell *plausible* from *correct*. Every scenario has
3+ interacting constraints and at least one trap a confident-but-wrong model states loudly.

**Everything is in this repo — exact prompts, full rubrics, raw model outputs, scored sheets:**

| What | Where |
|---|---|
| **Exact prompts + full scoring rubrics** (every item, inline) | [domain-suite.json](domain-suite.json) |
| Method, scoring protocol, trap index | [DOMAIN_SUITE.md](DOMAIN_SUITE.md) |
| **Four-way 27B quant hunt** (nvidia W4A16 / genesis INT4 / ThinkingCap / AEON W4A4) | [results/domain-suite-four-way-20260710.md](results/domain-suite-four-way-20260710.md) |
| nvidia W4A16 vs genesis INT4, per-item | [results/domain-suite-nvidia-vs-genesis-20260710.md](results/domain-suite-nvidia-vs-genesis-20260710.md) |
| Genesis vs Ornith 35B, per-item | [results/domain-suite-comparison-20260709.md](results/domain-suite-comparison-20260709.md) |
| Genesis baseline scoresheet | [results/domain-suite-genesis-20260709.md](results/domain-suite-genesis-20260709.md) |
| **Raw model responses** (unedited) | [results/nvidia-concurrent.json](results/nvidia-concurrent.json) · [results/aeon-concurrent.json](results/aeon-concurrent.json) · [results/domain-suite-genesis-20260709-raw.json](results/domain-suite-genesis-20260709-raw.json) · [results/domain-suite-ornith-20260709-raw.json](results/domain-suite-ornith-20260709-raw.json) |
| Automated per-item judge scores (Haiku 4.5) | [results/aeon-haiku-scores.json](results/aeon-haiku-scores.json) |

Run it yourself against any OpenAI-compatible endpoint:

```bash
python probe.py --probes-file domain-suite.json --no-judge --max-tokens 1600 \
  --base-url http://YOUR_ENDPOINT/v1 --model YOUR_MODEL
```

Scoring is 5/3/1 against each item's `rubric` field (anchors + red flags included per item).
Judge yourself, or wire `--judge-key` for Claude-as-judge.

## The 25-probe quality suite

The older general suite ([probes.json](probes.json)) — reasoning, coding, instruction
following, factuality, agent tasks — with Claude-as-judge. Used for the internal quality
scores cited on the benchmarks page (labeled there as an internal probe suite, not a
public standard benchmark).

## Hardware context

All local runs: 2× RTX 5060 Ti 16 GB (Blackwell SM_120), TP=2 over PCIe, 32 GB VRAM total.

- **genesis** (Qwen3.6-27B INT4 AutoRound, vLLM + MTP): **29.5 GB VRAM measured**
  (15.1 + 14.4 GB, 2026-07-10), GMU 0.90, 65K ctx.
- **nvidia W4A16** run: pinned at the 32 GB ceiling — CUDA graphs had to stay disabled
  for lack of VRAM headroom (eager mode), which is part of why it runs at ~16–23 t/s vs
  genesis's ~62–97 t/s. Exact per-GPU draw wasn't captured during the run; the
  graphs-blocked condition is noted in the four-way sheet.
- Per-model serving configs, flags, and throughput receipts:
  [inference-research](https://github.com/randomchaos7800-hub/inference-research).

## Honest limitations

- The domain-suite judge is rubric-anchored Claude (in-session or Haiku automated);
  ordering agreed across both judges on every comparison so far. A human domain-expert
  re-score of any sheet is welcome — the rubrics are written for exactly that.
- Scenario prompts are public, so they can be trained against. They're a judging aid
  for a human expert, not a leaderboard.

#!/usr/bin/env bash
# run_eval.sh — Full quality evaluation for a model on local proxy
#
# Usage:
#   ./run_eval.sh                          # full run, all benchmarks + all probes
#   ./run_eval.sh --probes-only            # just the 25 curated probes
#   ./run_eval.sh --benchmarks-only        # just MMLU/GSM8K/TruthfulQA
#   ./run_eval.sh --quick                  # probes + 20q benchmarks (fast)
#   ./run_eval.sh --base-url URL           # custom proxy URL
#   ./run_eval.sh --model NAME             # custom model name
#
# Results go to: ./results/YYYY-MM-DD_HHMM/

set -euo pipefail
cd "$(dirname "$0")"

# ── defaults ──────────────────────────────────────────────────────────────────
BASE_URL="http://localhost:8010/v1"
MODEL="local"
LIMIT=50
RUN_PROBES=true
RUN_BENCHMARKS=true

# ── args ──────────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --probes-only)      RUN_BENCHMARKS=false; shift ;;
    --benchmarks-only)  RUN_PROBES=false; shift ;;
    --quick)            LIMIT=20; shift ;;
    --base-url)         BASE_URL="$2"; shift 2 ;;
    --model)            MODEL="$2"; shift 2 ;;
    --limit)            LIMIT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# ── output dir ────────────────────────────────────────────────────────────────
TS=$(date +%Y-%m-%d_%H%M)
OUT="./results/${TS}"
mkdir -p "$OUT"

echo "╔══════════════════════════════════════════╗"
echo "║        Boundary Labs Model Eval          ║"
echo "╠══════════════════════════════════════════╣"
echo "║ Proxy:  $BASE_URL"
echo "║ Model:  $MODEL"
echo "║ Output: $OUT"
echo "╚══════════════════════════════════════════╝"
echo ""

T_START=$(date +%s)

# ── probes ────────────────────────────────────────────────────────────────────
if [ "$RUN_PROBES" = true ]; then
  echo "▶ Running quality probes (25 prompts + Claude judge)..."
  python3 probe.py --base-url "$BASE_URL" --model "$MODEL" --output-dir "$OUT"
  echo ""
fi

# ── benchmarks ────────────────────────────────────────────────────────────────
if [ "$RUN_BENCHMARKS" = true ]; then
  echo "▶ Running standardized benchmarks (${LIMIT}q each)..."
  python3 benchmark.py \
    --base-url "$BASE_URL" \
    --model "$MODEL" \
    --limit "$LIMIT" \
    --output-dir "$OUT"
  echo ""
fi

# ── combined summary ──────────────────────────────────────────────────────────
T_END=$(date +%s)
ELAPSED=$(( T_END - T_START ))

echo "══════════════════════════════════════════"
echo "Done in ${ELAPSED}s. Results: $OUT"
echo ""
echo "Files:"
ls "$OUT"

# Combine reports into one file if both ran
if [ "$RUN_PROBES" = true ] && [ "$RUN_BENCHMARKS" = true ]; then
  {
    echo "# Full Eval — $MODEL — $TS"
    echo ""
    cat "$OUT/probe_report.md" 2>/dev/null || true
    echo ""
    echo "---"
    echo ""
    cat "$OUT/benchmark_report.md" 2>/dev/null || true
  } > "$OUT/full_report.md"
  echo "Combined: $OUT/full_report.md"
fi

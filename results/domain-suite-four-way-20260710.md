# Qwen3.6-27B quant hunt — four-way domain suite (2026-07-10)

Goal: find a 27B quant that beats **genesis** on quality without losing production speed.
Result: **none did.** Genesis is the frontier on 2×16GB consumer Blackwell.

Method: 15 domain-expert scenarios (logistics/traffic/restaurants), thinking off,
concurrent generation, judged blind by **OpenRouter Claude Haiku 4.5** (same judge + same
condition for every model). Raw responses: `*-concurrent.json`. Per-item scores:
`*-haiku-scores.json`.

| Model | Recipe | Quality (Haiku, /5) | Speed | Verdict |
|---|---|:---:|---|---|
| **nvidia** Qwen3.6-27B-NVFP4 | NVFP4 **W4A16** (16-bit act) | **3.93** | ~16–23 t/s | quality champion, unusably slow (Marlin emulation; graphs VRAM-blocked, no MTP) |
| **genesis** Qwen3.6-27B-INT4 | INT4 AutoRound + MTP | **3.73** | ~62–97 t/s | **production frontier** |
| **ThinkingCap** 27B-int4 | INT4 AutoRound + MTP | **3.67** | = genesis | wash with genesis, no upgrade (v1; v2 planned) |
| **AEON** 27B-NVFP4-MTP-XS | NVFP4 **W4A4** (4-bit act) | **3.40** | ~69 t/s | fast + 122K ctx, lowest quality — native FP4 costs quality |

(genesis in-session Claude judge scored it 3.73 too; nvidia +0.40 in-session vs +0.20 Haiku —
both judges agree on ordering.)

## The proven boundary

Quality tracks **activation precision**, inversely to speed:
- W4A16 (16-bit act) = best quality, slowest (no native kernel → emulation).
- W4A4 (4-bit act) = fastest, lowest quality.
- INT4 AutoRound + MTP = the sweet spot, and **genesis already sits on it.**

You cannot have W4A16 quality at native-FP4 speed on this hardware. The nvidia W4A16's
+0.20 edge isn't worth 3–4× the latency; AEON's native-FP4 speed costs 0.33 quality below
genesis; ThinkingCap's "enhanced base" didn't show up as domain-suite gains.

Only remaining upgrade paths, both marginal: ThinkingCap **v2** when it ships, or a
hand-tuned INT4 (smaller group size / act-order). Dead ends recorded so we don't re-chase.

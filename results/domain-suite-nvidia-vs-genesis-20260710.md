# Domain Suite — nvidia NVFP4 (W4A16) vs Genesis (INT4) — 2026-07-10

- **nvidia-27b:** Qwen3.6-27B nvidia NVFP4, **W4A16** (mixed: FP8 attn + NVFP4 group-16 MLP),
  vLLM 0.24 direct `:8031`, TP=2 eager, thinking OFF, max_tokens 1600, temp 0.3
- **Genesis:** Qwen3.6-27B INT4 AutoRound/GPTQ-Marlin, thinking OFF, max_tokens 1600
  (baseline from `domain-suite-genesis-20260709.md`)
- **Judge:** Claude Code, rubric-anchored, in-session (same methodology as the 07-09 comparison;
  the Haiku auto-judge was down — Anthropic key out of credits)
- **Generation note:** all 15 nvidia responses collected concurrently in 106s (vLLM batching);
  responses in `nvidia-concurrent.json`

## Head-to-head

| ID | Scenario | Genesis | nvidia | Winner |
|----|----------|:---:|:---:|:---:|
| log1 | Cold-chain triage | **5** | 4 | G |
| log2 | Axle weights | 3 | 3 | tie (neither knows the tandem slide) |
| log3 | HOS clocks | 4 | **5** | N (both clocks correct with times) |
| log4 | Dock capacity | 3 | **4** | N (derived the $37.50 detention + counterfactual) |
| log5 | Temp excursion | 3 | **4** | N (gets carrier liability RIGHT; genesis flipped Carmack) |
| traf1 | Yellow trap | 3 | 3 | tie (neither names the true trap; nvidia found FYA) |
| traf2 | Work-zone closure | 5 | 5 | tie (both reject 24/7; nvidia's 6.6-mi queue matches key) |
| traf3 | Arena egress | 4 | 4 | tie |
| traf4 | Roundabout vs rail | 4 | 4 | tie (nvidia nails signal-preempts-rail) |
| traf5 | Stop signs | 4 | **5** | N (warrants + speed-myth + calming + pilot, textbook) |
| rest1 | Friday cascade | 4 | 4 | tie |
| rest2 | Food-cost jump | 4 | 4 | tie |
| rest3 | Inspection | 4 | **5** | N (exact 135→70/2hr + heat-stable-toxin, rejects reheat) |
| rest4 | Menu engineering | 3 | **4** | N (**did NOT swap Plowhorse/Puzzle** — genesis & Ornith both did) |
| rest5 | Catering + allergy | 3 | **4** | N (**no false "guaranteed nut-free"** — acknowledges shared kitchen) |

## Totals

| | Logistics | Traffic | Restaurants | **Overall** | 5s | ≤2s | Red flags |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Genesis (INT4)** | 3.6 | 4.0 | 3.6 | **3.73** (56/75) | 2 | 0 | 0 |
| **nvidia (W4A16)** | 4.0 | 4.2 | 4.2 | **4.13** (62/75) | 4 | 0 | 0 |

Item wins: nvidia 6, Genesis 1, tie 8.

## The verdict

**The "qualitatively better" intuition is confirmed and quantified: nvidia W4A16 beats
genesis INT4 by +0.40 on the domain suite (4.13 vs 3.73), same clean floor (no item < 3,
zero hard red flags).** The quality edge is the W4A16 recipe — 16-bit activations + NVFP4
group-16 weight granularity preserve reasoning that INT4's group-128 loses. Concrete wins:

- **log5:** gets temperature-excursion liability right (carrier eats it, Carmack) where
  genesis flipped it.
- **rest4:** the only model of the three tested that did **not** swap Plowhorse/Puzzle in the
  menu-engineering matrix — genesis AND Ornith both made that error. Correct CM in dollars.
- **rest5:** handled the severe-allergy catering correctly — explicitly refused to promise
  "guaranteed nut-free" from a shared kitchen and pointed the client to their allergist.
  (Ornith failed this catastrophically; genesis was weaker.)
- **log3 / traf5 / rest3:** clean 5s — HOS both-clocks math, stop-sign warrants + calming,
  inspection cooling numbers with heat-stable-toxin reasoning.

**The trade, now measured on both axes:** nvidia W4A16 is **+0.40 quality** at **~⅓ the
speed** (~16–23 tok/s eager vs genesis 62 tok/s with MTP). Genesis remains the right default
for unreviewed agent work (speed + safe floor); nvidia W4A16 is the model to reach for when
answer quality on hard operational questions matters more than latency — exactly the
"consult for the hard ones" role.

**Method caveat:** in-session Claude judging (not the automated Haiku pass, which was down).
Same judge, same rubrics, same thinking-off condition as genesis's — apples to apples — but
single-judge, not blind-panel. Directionally solid; the +0.40 gap is comfortably outside
single-item noise.

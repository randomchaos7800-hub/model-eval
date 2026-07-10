# Domain Suite — Genesis scored run (2026-07-09)

- **Model:** genesis (Qwen3.6-27B GPTQ INT4, vLLM Genesis-patched) via fleet proxy `:8010`
- **Config:** temperature 0.3, max_tokens 1600, `probe.py --probes-file domain-suite.json --no-judge`
- **Judge:** Claude (rubric-based stand-in; Dino's expert review may adjust — scores anchored to each item's rubric in `domain-suite.json`)
- **Raw answers:** `results/probe_results.json` (this run)

## Scorecard

| ID | Scenario | Score | Act on it? | One-line verdict |
|----|----------|:---:|:---:|---|
| log1 | Cold-chain triage | **5** | yes | Perfect triage; engaged the reefer-#2 judgment call with reasoning (can hold 34-38°F but declined the risk) |
| log2 | Axle weights | **3** | no | Found the drive-axle violation, refused shipper pressure — but never mentions the free tandem slide (prescribes a 3-hour reload) and fabricates a "steer axle is overloaded" violation at 11,900 |
| log3 | HOS clocks | **4** | yes | Both clocks computed correctly incl. the 45-min deadhead, right conclusion, viable alternatives; invented "a break pauses the 11-hour clock" (inert, in a rejected option) |
| log4 | Dock capacity | **3** | no | Did the 420-vs-360 math, right slip choice — then idled the forklift 10 min and delivered a plan that breaches the SLA by 20 min when a zero-breach schedule (300 min must-do) was trivially feasible |
| log5 | Temp excursion claim | **3** | no | Evidence/notify/don't-hide all right; flips Carmack liability (says shipper eats it unless carrier negligence proven — backwards for in-transit damage in carrier custody) |
| traf1 | Yellow trap | **3** | no | Never finds the yellow trap; builds a plausible platooning/gap story, no FYA; protected-only offered with correct trade-offs (would incidentally fix it) |
| traf2 | Work-zone closure | **5** | yes | Queue math beyond spec (1,400 veh, 5.3 mi, clears ~01:00), taper windows spec'd, school constraint drives the answer, caught the prompt's own arithmetic wrinkle |
| traf3 | Arena egress | **4** | mostly | Flush plans, LPI, flaggers, metrics all present; ped surge runs concurrent with vehicle flush instead of explicitly first |
| traf4 | Roundabout vs rail | **4** | yes | Found the trap: spillback-into-circle fully reasoned, signal-interlock recommendation with fail-safe logic; missing the track-clearance FLUSH half of preemption (only prevents entry) |
| traf5 | Stop signs | **4** | yes | "Stop signs don't control speed" fully argued as a memo, pilot + politics handled; no MUTCD warrant criteria, no unwarranted-device liability point, one wince line ("10-15 over is acceptable") |
| rest1 | Friday cascade | **4** | yes | Right priority order, decisive discards, refrigeration call; self-contradicts on the TCS window and no fire-staging for the 14-top |
| rest2 | Food-cost jump | **4** | yes | Kills vendor story with exact arithmetic (2% ≈ 0.5-0.6 pts), theoretical-vs-actual shrinkage gap per item as centerpiece; never tests menu-mix, misses receiving fraud |
| rest3 | Inspection | **4** | yes* | Nails the trap (heat-stable toxins, discards soup in front of inspector, rejects KM); states stage-one cooling as 4 hrs instead of 2 (*fix that number) |
| rest4 | Menu engineering | **3** | with fixes | CM math perfect, thresholds explicit, ravioli nuance excellent — but swapped Plowhorse/Puzzle labels (duck and fish & chips exactly backwards); actions match the TRUE classes |
| rest5 | Catering + allergy | **3** | **NO** | Operational protocol genuinely good (facility-processed audit, dedicated lead/tools, sealed labels) — but the client email promises an "ALLERGEN-FREE ZONE" with zero shared-kitchen disclosure (red-flag class), and transport temp control is absent |

## Domain means

| Domain | Mean | Read |
|---|:---:|---|
| Logistics | **3.6** | Strong triage instincts; weak on trade-craft (tandem slides) and legal frameworks (Carmack) |
| Traffic | **4.0** | Best domain — capacity/queue math is genuinely strong; missed the one pure domain-lore item (yellow trap) |
| Restaurants | **3.6** | Right instincts everywhere; loses points on exact standards (cooling numbers), framework vocabulary, and legal-communication discipline |
| **Overall** | **3.73 / 5** (56/75) | |

## Pattern findings

1. **Genesis reasons well and knows unevenly.** Where the scenario rewards *structured
   reasoning over given numbers* (traf2, log4 math, rest4 math), it performs at or near
   expert level. Where it rewards *trade lore* (tandem slides, yellow trap/FYA, matrix
   vocabulary, cooling stage times), it confabulates a plausible substitute — which is
   exactly the failure class this suite was built to expose, and it reads convincingly.
2. **Execution vs analysis gap (log4):** it computed the constraint correctly and then
   violated it in its own schedule. Plans need checking against the model's own math.
3. **Legal/liability is its weakest layer:** Carmack flipped (log5), allergy overpromise
   in writing (rest5), fabricated steer violation (log2). Never let it write anything
   liability-adjacent unreviewed.
4. **Zero scale-dodging / concealment suggestions** anywhere — its compliance-ethics
   instincts are consistently right even when its compliance facts are wrong.
5. Two answers benefited from the 1600-token rerun vs the truncated 512 first run
   (log2's reload direction corrected, log3 gained the deadhead in the math) — cap
   matters; keep 1600 for this suite.

# Domain Suite — Genesis vs Ornith (2026-07-09)

- **Genesis:** Qwen3.6-27B GPTQ INT4, vLLM Genesis-patched — via proxy `:8010`, max_tokens 1600, temp 0.3
- **Ornith:** Ornith-1.0-35B-AEON-Ultimate NVFP4, vLLM 0.23 — direct `:8030`, max_tokens 4000, temp 0.3
  (thinking enabled per prod config; log3 required `enable_thinking:false` — see method notes)
- **Judge:** Claude, rubric-anchored (same rubrics, same session, Ornith scored blind to genesis scores per item)
- **Raw:** `domain-suite-genesis-20260709-raw.json` · `domain-suite-ornith-20260709-raw.json`

## Head-to-head

| ID | Scenario | Genesis | Ornith | Winner | Delta note |
|----|----------|:---:|:---:|:---:|---|
| log1 | Cold-chain triage | **5** | 4 | G | Both correct on frozen; Ornith made the bolder (also-sanctioned) call to ship produce on reefer #2 with transparency — but truncated mid-customer-comms |
| log2 | Axle weights | 3 | **4** | O | Ornith: clean violation isolation, no fabricated steer violation, lighter fix (2-3 pallets), signed-release script. Neither model knows the tandem slide |
| log3 | HOS clocks | **4** | 1 | G | Ornith misread 8.5 driven as 4.5, invented "break resets driving clock," and RECOMMENDED an illegal dispatch ("delay pickup to 19:00 — the 14-hour window resets") |
| log4 | Dock capacity | 3 | **5** | O | Ornith ran the perfect schedule: dependency named, zero idle, both SLA loads at exactly 19:00, $37.50 detention with counterfactual. Genesis breached the SLA unnecessarily |
| log5 | Temp excursion | 3 | **4** | O | Ornith gets liability RIGHT (carrier eats it) where genesis flipped Carmack; genesis had better evidence/salvage mechanics |
| traf1 | Yellow trap | 3 | **4** | O | Neither names the trap; Ornith recommends FYA with the correct preserve-coordination rationale — genesis never found FYA |
| traf2 | Work-zone closure | **5** | 1 | G | Ornith did the same queue math then RECOMMENDED 24/7 closure anyway, laundered 1,400 queued vehicles as "~30 min delay, within DOT thresholds" (fabricated), and signed the detour past the school |
| traf3 | Arena egress | 4 | **5** | O | Ornith's ops-document is the best answer either model produced: explicit pedestrian all-red phase, queue-detection triggers, 4-event pre/post metrics |
| traf4 | Roundabout vs rail | **4** | 2 | G | Ornith saw spillback, then discounted it ("continuous flow minimizes gridlock" into a blocked exit), proposed 150-200 ft storage inside a fixed 280, called the SIGNAL rail-vulnerable |
| traf5 | Stop signs | **4** | 1 | G | Ornith's lead fix: RAISE the limit to 35 and tell residents the street is "safer and faster to drive"; offers to install the unwarranted stops anyway as backup |
| rest1 | Friday cascade | **4** | 2 | G | Ornith's delivered fraction was excellent (discard logs, transparent menu pivot) but truncated before staffing/14-top/FOH — not an actionable plan |
| rest2 | Food-cost jump | 4 | 4 | tie | Same theoretical-vs-actual centerpiece; Ornith adds the receiving-fraud vector genesis missed; both miss menu-mix |
| rest3 | Inspection | 4 | **5** | O | Ornith: exact cooling numbers (135→70/2hr — genesis said 4hr), full heat-stable toxin roster, better KM script |
| rest4 | Menu engineering | **3** | 2 | G | BOTH swap Plowhorse/Puzzle identically (Qwen-family vocabulary confusion?); Ornith argues CM-dollars better but truncates after one item's action |
| rest5 | Catering + allergy | **3** | 1 | G | Ornith writes the client "our food is GUARANTEED nut-free" — the literal forbidden word — while acknowledging it's a shared kitchen |

## Totals

| | Logistics | Traffic | Restaurants | **Overall** | 5s | ≤2s | Hard red flags |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Genesis** | 3.6 | 4.0 | 3.6 | **3.73** (56/75) | 2 | 0 | 0 |
| **Ornith** | 3.6 | 2.6 | 2.8 | **3.00** (45/75) | 3 | 6 | 4 |

Item wins: Genesis 8, Ornith 6, tie 1.

## The story

**Inverted profiles, again.** Same shape as the LangChain head-to-head (Ornith owns sequential
composition, DeepSeek owns reasoning): here **Ornith has higher highs and catastrophic lows**.
Its three 5s beat anything genesis wrote on those items — the dock schedule is flawless, the
egress plan is professional-grade, the cooling numbers are exact. And its four hard red flags
are the worst answers in the whole experiment:

1. Recommended an illegal dispatch off a fabricated HOS reset (log3)
2. Endorsed the 24/7 closure and routed the detour past the school at dismissal (traf2)
3. "Raise the speed limit and tell residents it's safer" (traf5)
4. "Guaranteed nut-free" in writing to a severe-allergy client from a shared kitchen (rest5)

**Genesis never scored below 3. Ornith scored ≤2 on six of fifteen.** For an unsupervised
agent backend answering operational questions, the floor is the product metric, not the
ceiling — variance is risk. Genesis is the model you let answer unreviewed; Ornith is the
model you consult for the hard ones and then check.

**Confidence is anti-correlated with correctness on Ornith's failures.** Every red-flag answer
is fluently argued with fabricated support (invented DOT delay thresholds, invented HOS resets,
"safer and faster"). This is precisely the failure class the suite was built to surface, and
it's invisible without domain expertise.

## Method notes (operational findings, themselves useful)

- **local-proxy mangles long non-streaming responses.** The full suite through `:8010` returned
  empty content for most items while direct `:8030` calls worked — needs a proxy fix before
  any agent relies on long completions through it. (Genesis's 1600-token answers passed; the
  failure appeared on Ornith-length responses.)
- **Ornith's thinking burns the budget.** With the prod reasoning-parser config, several items
  returned content=None (everything eaten by an unclosed think block); log3 did this 7 times
  consecutively and only answered with `enable_thinking:false`. Two answers (rest1, rest4)
  truncated mid-plan even at 4000 tokens — scored as delivered.
- **AEON's spurious-empty quirk** (cf. Crush tool-steering issue): identical calls
  sometimes return an empty message; retry-on-empty added to probe.py.
- Both models swap Plowhorse/Puzzle in the menu-engineering matrix — possibly a shared
  Qwen-lineage training artifact worth testing on other Qwen-family models.

# Domain Expert Suite — logistics · traffic · restaurants

15 scenarios (5 per domain) for testing local/OS models against problems where the
**judge has real domain expertise**. The 25-probe suite measures general quality with an
LLM judge; this suite is different on purpose: every item is a messy operational
situation with interacting constraints, and the scoring rubric encodes what a
practitioner checks — so a human expert (Dino: logistics, traffic, restaurants) can
tell *plausible-sounding* apart from *actually right* in under a minute per answer.

## Design principles

- **Interacting constraints, not trivia.** Every scenario has 3+ constraints that
  collide (a clock, a capacity, a rule, a person). Single-lookup answers can't score 5.
- **A trap per item.** Each scenario contains at least one thing a confident-but-wrong
  model gets loudly wrong (e.g., "gross weight is legal so the load is legal",
  "reheating the soup fixes it", "stop signs slow traffic"). Rubric RED FLAGS list them.
- **Expert-checkable specifics.** Rubrics reference numbers a practitioner knows
  (34,000-lb tandem limit, 135→70→41°F cooling, ~1,300 veh/hr work-zone throughput,
  contribution margin in dollars) so scoring is anchored, not vibes.
- **Judgment calls allowed.** Some items (reefer #2, roundabout-vs-signal) accept more
  than one answer *if the reasoning engages the controlling constraint*. The rubric says
  which constraint is controlling.

## Scoring

Human-judged, 5/3/1 per item (anchors in each rubric):

- **5** — a practitioner would sign off; controlling constraints identified, specifics right
- **3** — right general shape, but shallow where it matters or one significant miss
- **1** — wrong decision, fabricated rule, or a RED FLAG statement

Suite score = mean per domain + overall. Track per-model: score, red-flag count, and
"would I act on this answer?" (yes/no) — the last column is the real product question.

## Running

```bash
# collect model answers only (judge yourself)
python probe.py --probes-file domain-suite.json --no-judge

# one domain at a time
python probe.py --probes-file domain-suite.json --no-judge --category logistics
python probe.py --probes-file domain-suite.json --no-judge --category traffic
python probe.py --probes-file domain-suite.json --no-judge --category restaurants
```

Default endpoint is the fleet proxy (`:8010`); pass `--base-url`/`--model` to point at a
specific backend. Answers land in `results/` — score against the `rubric` field of each
item in `domain-suite.json`.

## Items

| ID | Domain | Scenario | The trap |
|----|--------|----------|----------|
| log1 | logistics | Reefer down, 3 loads, cold-chain triage | putting frozen at risk / not calling customers tonight |
| log2 | logistics | Legal gross, illegal drive axles at 35,600 | "under 80k = legal"; wrong tandem-slide direction |
| log3 | logistics | HOS math on a hot load (11-hr vs 14-hr clocks) | treating the 30-min break as extending the 14 |
| log4 | logistics | 3 doors, 1 forklift, 360 min capacity vs 420 min demand | scheduling 420 minutes into 360 without noticing |
| log5 | logistics | Temp excursion on strawberries mid-route | delivering quietly; "temp recovered, no issue" |
| traf1 | traffic | Left-turn crash spike after lead-lag retiming | missing the yellow trap; "longer yellows" as fix |
| traf2 | traffic | 2-of-3 lane closure, 2,700 vph demand vs 1,300 capacity | 24/7 closure + detour past a school at dismissal |
| traf3 | traffic | 9,000-seat arena egress on a 2x2 grid | optimizing cars while ignoring the pedestrian surge |
| traf4 | traffic | Roundabout vs signal, rail crossing 280 ft away | ignoring queue spillback onto tracks / preemption |
| traf5 | traffic | Residents demand stop signs for speeding | "stop signs will slow them down" |
| rest1 | restaurants | Friday rush: 86'd salmon + warm walk-in + short line + 14-top | walk-in triaged last; no TCS time logic |
| rest2 | restaurants | Food cost 28%→34%, flat sales, vendors +2% | accepting the vendor story; skipping theoretical-vs-actual |
| rest3 | restaurants | Inspector mid-rush: 0 ppm sanitizer + 44°F day-old soup | "reheating kills everything" (heat-stable toxins) |
| rest4 | restaurants | Menu engineering incl. a beloved money-loser | ranking by food-cost % instead of CM dollars |
| rest5 | restaurants | 180 covers + 120-guest offsite + tree-nut allergy | guaranteeing zero cross-contact in writing |

## Baseline discipline

Run every model on identical prompts (temperature per your standard bench config),
score blind if possible (shuffle which model produced which answer before judging),
and keep the scored sheets in `results/` next to the raw runs. When comparing local
models to a frontier reference, judge the frontier answer with the same rubric —
several of these items catch big models too.

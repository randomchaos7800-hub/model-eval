# Mac mini quant hunt — Ornith-9B vs Bonsai-27B family (2026-07-16)

Goal: find a model that runs well on a 16GB unified-memory Mac mini (MLX) for small-model
testing. Result: **Ornith-1.0-9B-4bit stays the live default** — smallest model on the list,
still beats both Bonsai 27B builds on quality, and neither Bonsai build's speed edge is worth
its failure profile.

Method: same 15-scenario domain-expert suite (logistics/traffic/restaurants), thinking off,
judged directly against the suite's rubrics (Anthropic judge key was out of credits — see
`feedback_direct_judge` in project memory). Genesis row is the existing 2026-07-09 tower
baseline (different hardware, included for reference — same Qwen3.6-27B base as Bonsai, but
quantized via GPTQ INT4 rather than Prism ML's ternary/binary method).

| Model | Recipe | Quality (/5) | Speed | Verdict |
|---|---|:---:|---|---|
| **genesis** (tower, reference) | Qwen3.6-27B GPTQ INT4 | **3.73** | ~97 t/s (dedicated GPU) | same base as Bonsai, light quant — clean reference point |
| **Ornith-1.0-9B-4bit** | MLX uniform 4-bit, 9B | **3.00** | ~18.66 t/s | **live default** — smallest model, still ahead of both 27B Bonsai builds |
| **Ternary-Bonsai-27B** | Prism ML ternary, 1.71 bpw, 8.49GB | **2.93** | ~12.16 t/s | not adopted |
| **Bonsai-27B** | Prism ML binary, 1.125 bpw, 3.9GB | **2.47** | ~20.33 t/s (fastest of the three) | not adopted despite raw speed |

## The failure pattern

Both Bonsai builds fail two of the same three scenarios identically, regardless of bit-width:

- **traf4** (roundabout vs. signal at a rail crossing): both recommend the roundabout —
  the wrong answer — missing that signals support rail preemption and roundabouts don't.
  Genesis gets this right, fully reasoning through the trap.
- **log3** (Hours-of-Service clock math): both get stuck in identical confusion over
  whether a 30-min break counts toward the 14-hour window, and both run out of token
  budget mid-reasoning without ever reaching a dispatch decision. Genesis computes both
  clocks correctly and reaches a viable answer.
- **rest5** (severe allergy + shared kitchen): both write an unconditional written
  guarantee of zero cross-contact — a real liability red flag, and *more* explicit in the
  2-bit build than the 1-bit one (more bits, same wrong answer, more confidence behind
  it). Weaker evidence than the other two: Genesis also gets marked non-actionable here
  (implies an undisclosed allergen-free zone), so this scenario looks more like a hard
  trap in the suite itself than a Bonsai-specific defect.

**Reading the two clean failures against the Genesis reference**: since Genesis shares
Bonsai's exact base model (Qwen3.6-27B) but not its quantization method, and clears both
traps that Bonsai fails identically at two different bit-widths, the evidence points at
something specific to Prism ML's extreme low-bit compression method damaging a capability
that survives ordinary GPTQ-style quantization fine — not damage that scales with bits
within Bonsai's own lineage (more bits didn't help there), and not something baked into
the shared parent model's training before any quantization happened at all.

## Fluent-and-wrong is the risk that matters here

All three models are fluent and well-formatted even when wrong — that's the actual risk,
not raw capability. A model that hedges is annoying; a model that puts a liability-grade
guarantee in writing is potentially dangerous. Neither Bonsai build goes live on speed
alone. Re-test if a newer Prism ML checkpoint drops.

Build notes (Prism ML fork, cmake/Metal toolchain gotchas, Xet download hang workaround)
recorded in citadel `infrastructure.md` / `case-law.md`, not duplicated here.

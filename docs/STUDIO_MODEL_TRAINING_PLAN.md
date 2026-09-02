# StudioRam Model Training Plan

> How to go from "call Imagen with a prompt string" to owning a model stack that renders
> the AO World Engine's simulation as consistent, animated, stylized frames.

**Status:** Plan / RFC. Nothing here is implemented yet.
**Audience:** engineering, plus studio and capital partners evaluating the build.

---

## 1. Where StudioRam actually is today

Before planning a model, an honest read of the current renderer.

| Layer | Current implementation | Where it lives |
|-------|------------------------|----------------|
| Still images | Hosted Vertex AI Imagen 3, prompt-only | `api/api_simulation.py:2654`, `api/studioram/scene_generator.py` |
| Video | Hosted Veo 3 preview, prompt-only, async poll | `api/api_simulation.py:2733` |
| Style control | A hardcoded prose block, `"85% grayscale... ONLY cyan (#00CED1)"` | `api/api_simulation.py:2664` |
| Character identity | None | — |
| Keyframe control | None | — |
| Model ownership | None, all third-party hosted | — |

Three consequences follow from that table, and they are the whole reason to train something.

**Style is a suggestion, not a constraint.** The look is a paragraph of English handed to a
general-purpose model. Two calls with the same prompt give two different looks. There is no
mechanism that can make the model obey a style, only ask it to.

**Characters are not the same person twice.** There are 823 NPCs with fixed identities, factions,
and personality vectors. The renderer cannot draw any of them consistently, because a prompt
cannot carry a face. This is the single biggest gap between what the engine knows and what
StudioRam can show.

**The world engine's best asset is being thrown away.** The simulation already computes, for any
tick, exactly who is where, doing what, in what weather, with what mood, at what event severity.
That is a complete, structured, machine-readable shot description. Today it gets flattened into
a sentence and handed to a text-to-image API. Almost all of the signal is discarded at that step.

---

## 2. The data question, answered directly

The plan as described was: download nearly every popular anime and every manga adapted from it,
train on all of it. That part does not work, and it is worth being precise about why, because the
reason also points at the better plan.

**It is unlicensable.** A model trained on scraped commercial anime cannot be sold, licensed to a
studio, used in a funded production, or included in due diligence. Japanese publishers and the
Content Overseas Distribution Association enforce actively. The moment StudioRam has revenue or
a raise, that training set becomes the first thing diligence finds and the last thing it clears.
Access to studios and capital is stated as an advantage here. Scraped training data is precisely
the thing that destroys both.

**It produces a worse model than expected.** Training on every popular anime does not yield a
model that can do any style. It yields the *average* of all of them, a generic mid-2010s TV-anime
look that a dozen public checkpoints already produce for free. Distinctiveness comes from a narrow,
curated, coherent set. The goal is a house style nobody else has, and breadth is the enemy of that.

**Finished video cannot teach keyframing.** This is the technical point that matters most. The
stated goal is generating *keyframes* that an animator then works from. Broadcast anime is the
finished output: composited, inbetweened, color-corrected, 3-frame-held. It contains no labeled
keyframes. You cannot learn "which drawing is the key pose" from footage where every frame looks
alike. The data that teaches keyframing is the production intermediate: genga (key drawings),
douga (inbetweens), layouts, timing sheets, model sheets. That data exists only inside studios.

**So the studio access is the plan, not a side benefit.** A licensed pipeline into even two or
three studios' production archives gives paired keyframe/inbetween data that no scraper can
obtain at any price. That is a genuine moat. Scraping is the commodity path; licensing is the
defensible one, and it is the one already within reach.

### The data plan that does work

| Tier | Source | What it trains | Volume needed |
|------|--------|----------------|---------------|
| A | Studio license: genga, douga, layouts, timing sheets | Keyframe selection, inbetweening, timing | 10k–100k paired drawings |
| B | Studio license: model sheets, turnarounds, expression sheets | Character identity adapters | 20–200 images per character |
| C | Commissioned work-for-hire from contract artists | The house style, owned outright | 2k–10k images |
| D | Public-domain and CC-licensed animation, permissive datasets | Base-layer pretraining reinforcement | Opportunistic |
| E | Own synthetic output, human-curated | Later self-distillation rounds | Grows over time |

Tier C is the cheapest way to start and the one with zero legal ambiguity. Commissioning a small
team of artists to produce a few thousand images in one deliberately designed style, under
work-for-hire contracts, buys a style that is legally yours forever. At typical rates this is a
five-to-low-six-figure line item, which is far less than the compute budget being contemplated,
and it de-risks everything downstream.

Every asset entering the training set gets a provenance record: source, license, contract
reference, date, and rights term. This is non-negotiable infrastructure, not paperwork. It is
what makes the model sellable later.

---

## 3. What kind of model to train

The answer is not one model. It is a stack of five layers, each cheap and independently useful,
each one gating the next. Do not train a foundation model from scratch. That is a $5M–$50M
exercise that buys no advantage, because the general capability is a commodity and the
advantage is entirely in the layers above it.

```
  Layer 5   Audio                      later, likely licensed not trained
      ▲
  Layer 4   Temporal / inbetweening    keyframe pair → animated sequence
      ▲
  Layer 3   Structural control         engine state → pose, depth, layout conditioning
      ▲
  Layer 2   Character identity         one adapter per recurring NPC
      ▲
  Layer 1   Style adapter              the house look, in weights not in prose
      ▲
  Layer 0   Base weights               permissively licensed open checkpoint, frozen
```

### Layer 0: base weights

Pick a commercially licensed open image model and freeze it. The selection criteria are license
terms first, adapter ecosystem second, quality third. It must be a license that permits
commercial output and downstream distribution without a revenue clause, verified by counsel, and
re-verified before any funded production ships. This layer is a dependency, not an asset.

### Layer 1: style adapter — the house look

A LoRA or DoRA adapter trained on the Tier C commissioned set. This is the layer that replaces
the hardcoded `"85% grayscale... ONLY cyan"` prompt with actual learned weights. The difference
is categorical: a prompt asks, an adapter constrains.

Realistic scope: 2,000–5,000 curated images, 8 GPUs, one to two days per run, perhaps fifteen
runs to find the right recipe. This is the smallest useful deliverable in the whole plan and it
should be built first, because it is the gate for everything else. If the style adapter does not
produce a look that is visibly, consistently distinct from what a public checkpoint gives, no
amount of further spend fixes that.

### Layer 2: character identity adapters

One small adapter per recurring NPC, trained on that character's model sheet and turnaround.
20–200 images each, minutes to an hour of GPU time each. Adapters compose with the style adapter
at inference, so the same character renders correctly in the house style, in any pose, at any
tick.

This is what closes the biggest current gap. It also scales the right way: it is not needed for
all 823 NPCs. Build it for the 20–40 characters that carry the narrative, and let the rest render
as styled crowd from archetype conditioning alone.

### Layer 3: structural control — where the engine plugs in

This is the layer that makes StudioRam different from every other anime generator, and it is
worth being explicit about why.

The simulation already emits, deterministically, for any tick: NPC positions, location ID and
name, district, weather, hour, period, event type, event severity, participant list, and mood.
`computeWorldState(tick, npcs)` reproduces it exactly every time. That is not a prompt. That is a
shot specification, and it is available in unlimited quantity at zero marginal cost, perfectly
labeled, for every tick of every layer of the multiverse.

Layer 3 is a ControlNet-style conditioning branch that consumes that state directly. NPC positions
become a spatial layout map. Archetype and action become pose skeletons. District geometry becomes
a depth hint. Weather and hour become lighting conditioning. The model is then told where everyone
stands and what the camera sees, rather than asked in English.

Two things follow. First, output becomes reproducible: the same tick renders the same frame,
which is what makes a persistent world visually coherent across sessions. Second, the labeled
training pairs for this layer can be generated by the engine itself, which is an enormous
practical advantage over any competitor working from unlabeled video.

### Layer 4: temporal — keyframe to motion

This is the "banger keyframe, then hardcore animation" step, and it is the most expensive and
the least certain, which is why it is fourth and not first.

Two sub-problems, and they should not be conflated:

**Inbetweening.** Given key drawing A and key drawing B plus a frame count, produce the drawings
between them. This is a well-posed, narrow problem, it is exactly what Tier A studio data
supervises, and it is the one most likely to produce a tool studios will actually pay for. Model
shape: a video diffusion model or a flow-based interpolator conditioned on both endpoints and a
timing curve.

**Sequence generation.** Given a scene spec, produce a moving shot outright. Higher ceiling, much
higher cost, far more failure modes. Treat this as research, not roadmap.

Build inbetweening first. It has a customer, a supervised training signal, and a clear success
metric. Sequence generation should wait behind an explicit gate.

### Layer 5: audio

Defer. Voice, foley, and score are three unrelated problems with three unrelated datasets, and
none of them is on the critical path to the product. Voice in particular carries performer-rights
exposure that dwarfs the image-side questions. License off-the-shelf until the visual stack ships.

---

## 4. Compute and budget, realistically

Order-of-magnitude figures for planning, at roughly current market rates for rented H100-class
capacity. These are planning numbers, not quotes.

| Phase | Work | Scale | Wall clock | Rough cost |
|-------|------|-------|-----------|-----------|
| 1 | Style adapter, ~15 runs | 8 GPUs | 3–4 weeks | $10k–30k |
| 2 | Character adapters, 40 characters | 1–8 GPUs | 2 weeks | $2k–8k |
| 3 | Structural control branch | 16–32 GPUs | 4–8 weeks | $40k–120k |
| 4 | Inbetweening model | 32–64 GPUs | 8–16 weeks | $150k–500k |
| — | Data: commissioned art, licensing, annotation | — | ongoing | $100k–500k+ |
| — | Storage, eval, serving, staff | — | ongoing | varies |

Two observations worth internalizing. Phases 1 and 2 together are under $40k of compute and
deliver the two capabilities StudioRam most visibly lacks today. And across the whole program,
data acquisition costs more than compute. That ratio is normal for this kind of work and it is
another reason the scraping shortcut is a false economy: it trades the cheap resource for legal
exposure on the expensive one.

---

## 5. Phasing, with gates

Each phase has an exit criterion. Do not fund the next phase until the current one clears it.
The gates exist to make failure cheap.

**Phase 0 — Foundations.** No training. Build the data pipeline, the provenance ledger, the eval
harness, and the licensing contracts. Convert the world state into a formal conditioning
descriptor (see `schemas/keyframe_conditioning.json`). Refactor the renderer so the style block
is data rather than a string literal in `api_simulation.py`.
*Gate: a held-out eval set exists and the current hosted-API renderer scores against it.*

**Phase 1 — Style adapter.** Commission the Tier C set. Train the house style.
*Gate: blind human raters distinguish house-style output from a public checkpoint at high rates,
and style consistency across runs beats today's prompt-only baseline decisively.*

**Phase 2 — Character identity.** Adapters for the top 20–40 NPCs.
*Gate: the same NPC is recognizably the same character across 20 renders in varied poses,
lighting, and ticks.*

**Phase 3 — Engine-conditioned control.** Wire the simulation state into structural conditioning.
*Gate: rendering the same tick twice produces the same frame, and NPC placement in the frame
matches the simulation's positions.*

**Phase 4 — Inbetweening.** Requires Tier A studio data to be actually in hand.
*Gate: studio animators accept the generated inbetweens as usable production drawings at a
meaningful rate.*

**Phase 5 — Sequence and audio.** Only after 1–4 ship.

The honest read on sequencing: Phases 0 through 2 are near-certain to work, are cheap, and fix
the most visible current weaknesses. Phase 3 is the differentiated one and is where the engine's
value gets unlocked. Phase 4 depends entirely on securing studio data and should not be scheduled
until that contract is signed.

---

## 6. What to build in this repo next

Concrete, ordered, all Phase 0.

1. **`schemas/keyframe_conditioning.json`** — formal contract between the simulation and any
   renderer. Added alongside this plan.
2. **Extract the style block from code.** The `"85% grayscale... ONLY cyan"` literal at
   `api/api_simulation.py:2664` becomes a world-plugin style record, so a world's look is data
   and every world can define its own. This is a prerequisite for a per-world style adapter.
3. **Renderer backend interface.** One interface, three implementations: hosted Imagen (today),
   hosted Veo (today), and a local adapter-stack backend (later). Nothing above the interface
   should know which is in use.
4. **Conditioning exporter.** A function taking `(tick, npcs)` to a `keyframe_conditioning`
   document. This is both the inference input and the training-pair generator.
5. **Eval harness.** Fixed tick set, fixed prompts, scored for style consistency, character
   consistency, and prompt adherence. Without this there is no way to know whether a trained
   model is better than the API call it replaces.
6. **Provenance ledger.** Append-only record for every training asset: source, license, contract,
   rights term. Build it before the first asset arrives, not after.

Items 2 through 4 are worth doing regardless of whether any model is ever trained. They make the
current hosted renderer better and they are the seam that a trained model later slots into.

---

## 7. Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Studio data licensing falls through | Critical to Phase 4 | Gate Phase 4 on a signed contract; Phases 1–3 do not depend on it |
| Base model license changes or is revoked | High | Prefer permissive licenses, keep the base swappable, re-verify before shipping |
| House style is not distinctive enough | High | Phase 1 gate catches this for under $30k |
| Compute cost overrun on Phase 4 | High | Hard gate; do not start without Phase 3 shipped |
| Contamination of the training set with scraped material | Critical | Provenance ledger, and no asset trains without a record |
| Character adapters do not compose with style adapter | Medium | Tested at Phase 2 gate, before any Phase 3 spend |

The largest risk is not technical. It is starting at Phase 4 because it is the exciting one,
spending the compute budget before the style and character layers exist, and discovering that the
sequence model has nothing coherent to animate.

---

## 8. Summary

The instinct is right and the target is real. A model that renders a persistent simulated world
in a consistent, owned style, with consistent characters, driven by the engine's own state, is a
genuinely defensible product and nothing on the market does it.

Three corrections to the plan as described.

**Do not train on scraped anime and manga.** It is unlicensable, it makes the model unsellable,
it forecloses the studio relationships that are the actual advantage, and it produces a
less distinctive model than a small curated set would.

**Do not train one model.** Train a stack of adapters over a frozen permissive base. The first
two layers cost under $40k of compute and fix the two things StudioRam most visibly cannot do
today.

**The engine is the moat, not the model.** No competitor has a deterministic world simulation
that emits perfectly labeled shot specifications for free, forever. Layer 3 is where that becomes
a product. Prioritize it over the more glamorous video work.

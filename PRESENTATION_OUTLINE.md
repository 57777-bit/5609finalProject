# Final Project Presentation — Reference Outline

> **Purpose.** Slide-by-slide outline for the FP4 presentation. Adapt to your preferred deck tool (Google Slides, Keynote, PowerPoint). Talking-point time estimates assume a **5–7 minute** total slot.
>
> **Live demo URL.** https://57777-bit.github.io/5609finalProject/
> **Repo.** https://github.com/57777-bit/5609finalProject

---

## Slide 1 — Title (0:30)

**The Geography of Opportunity**
*How birthplace shapes the chance of climbing — and how the U.S. compares globally.*

CSCI 5609 Final Project · Spring 2026
Brandon Borzello · Harris Li · Qi Wu · Yiqi Huang

**Talking point:** "We built an interactive scrollytelling piece that asks two linked questions: how unequal is opportunity inside the U.S., and how does the U.S. as a whole stack up against its wealthy peers?"

---

## Slide 2 — The Question (0:30)

> *How much does where an American child grows up shape their adult economic outcomes — and how does the U.S. as a whole compare against its wealthy peers?*

Two acts:
- **Part I — The American Problem.** Within the U.S., mobility is sharply geographic.
- **Part II — The Global Perspective.** The U.S. as a whole sits below most of its wealthy peers.

**Talking point:** "We deliberately structure as local→global so the audience first feels the within-country spread, then is asked to weigh the U.S. against peer economies."

---

## Slide 3 — Data Sources (0:30)

| Dataset | Use |
|---|---|
| **Opportunity Atlas** (Chetty et al.) | County-level adult outcomes by parent income |
| **GDIM 2023** (World Bank) | Intergenerational immobility (IGE) by country |
| **SWIID v9.6** (Solt) | Pre/post-tax inequality (Gini) |
| **OECD Education at a Glance** | School funding centralization |
| **US Census TopoJSON Atlas** | County + state boundaries |

**Talking point:** "All public, all loaded statically — no backend. Counties at 10M-vertex Albers USA projection."

---

## Slide 4 — Tech Stack (0:30)

- **SvelteKit** + **Svelte 5 runes** (`$state`, `$bindable`, `$props`, `$effect`)
- **D3 v7** scales, axes, projections
- **topojson-client** for boundary tessellation
- **Vite** dev server, **GitHub Actions** for static deploy
- **GitHub Pages** hosting → live URL above

**Talking point:** "Sticky right panel with scrollytelling left panel — the chart stays anchored as the prose advances, so each narrative beat resolves against a visible mark."

---

## Slide 5 — Step 0 · Scrollymap (0:30) [DEMO]

County-level mobility map with **button-triggered animation** through three tiers:

> Stuck (red) → Treading water (amber) → Climbing (blue)

Toggleable to **state-bubble (Dorling)** view. Click a state → zoom to its counties.

**Talking point:** "The opening uses a Play button instead of a scroll trigger because scroll triggers were producing layout reflow races on fast scrolls. The button locks the section to 100vh and removes that bug class."

---

## Slide 6 — Step 1 · ScatterPlot (0:30) [DEMO]

Poor-children vs rich-children adult-rank by county.

- Diagonal = perfect mobility line.
- Color encodes the gap (teal → yellow → red).
- **Annotation:** the three counties with the largest mobility gap are labeled by name.

**Talking point:** "Distance from the diagonal is the mobility gap. The reddest, most-distant points get named on the chart so the prose has a target."

---

## Slide 7 — Step 2 · ChangeMap (0:30) [DEMO]

Change in upward mobility, **1978 → 1992 birth cohorts.** Animated transition from the 1978 baseline to the 1992 outcome, with counties revealing in order of largest absolute change.

- **Annotations:** SOUTH / MIDWEST region tags anchor regional prose claims to the map.

**Talking point:** "The animation reveals counties from the largest changes inward, so the eye is drawn first to where mobility moved most."

---

## Slide 8 — Step 3 · SchoolFunding (0:30) [DEMO]

Stacked bar: **Central/Federal vs. Local/State** education funding share, U.S. vs. five wealthy peers.

- **Annotation:** big "**X% local**" headline centered in the U.S. red segment.

**Talking point:** "This is the bridge from the American problem to the global perspective. The U.S. funds schools through local property tax — so the geography of opportunity is partly the geography of the tax base."

---

## Slide 9 — Step 4 · The Great Gatsby Curve (0:45) [DEMO]

Cross-country scatter: **after-tax Gini (x) vs. immobility IGE (y)**.

- Trend line: more inequality ↔ less mobility.
- **Annotations:** named country labels (U.S. in red), NORDIC BENCHMARKS caption, and a takeaway callout "**U.S. — high inequality, low mobility**" with a dashed leader to the U.S. dot.

**Talking point:** "This is the canonical Great Gatsby curve. The U.S. sits up and to the right — the worst quadrant on both axes."

---

## Slide 10 — Step 5 · Redistribution Dumbbell (0:45) [DEMO]

For 14 countries: **market Gini → disposable Gini** (after taxes/transfers).

- Each row's Δ is labeled in points.
- **Annotation:** headline contrasts U.S. redistribution against the strongest Nordic redistributor.

**Talking point:** "Same starting market inequality can land at very different places. Denmark cuts ~25 points; the U.S. cuts under 10. The institutional choice matters more than the starting condition."

---

## Slide 11 — Step 6 · Mobility League (1:00) [DEMO — show the morph]

Ranking of major economies by **intergenerational immobility (IGE)**.

- **Animation:** the same 20 countries from the Gatsby curve **morph** from scatter dots into a sorted bar ranking. (rect-with-rx interpolation: circles flatten into bars over ~1.2s.)
- **Annotations:** "**U.S. — rank N of 20**" callout on the U.S. bar, "▸ peer" tags on Canada / Sweden / U.K. / Japan (the four named peers in the prose), takeaway "**Nine wealthy peers rank above the U.S.**" with leader.

**Talking point:** "This is the closing chart, and the morph is intentional — it makes visible that the *same* 20 countries we just showed scattered against inequality are now ranked. The continuity from Step 4 to Step 6 is the whole argument: it's the same world, viewed two ways."

---

## Slide 12 — Design Decisions That Mattered (0:45)

1. **Two-act structure** (American problem → global perspective). Local-then-global lets the reader internalize within-country spread before weighing the U.S. against peers.
2. **Sticky right panel.** Chart stays anchored; prose advances on the left.
3. **Word–image binding.** When prose names a country, that row is visibly distinguished (deep-blue label, peer tag, leader line).
4. **Curated league.** Restricted to 20 major economies — random low-IGE outliers (Mauritius, Maldives) muddied the rich-peer framing.
5. **Button trigger over scroll trigger** for the opening animation — fixes layout reflow on fast scrolls.

**Talking point:** "Most of these decisions came from things that broke. The button trigger replaced a scroll trigger that raced. The curated league replaced a naive 'all countries' view that buried the U.S. in noise."

---

## Slide 13 — Animation & Interaction Highlights (0:30)

- **Morph animation** (scatter → bar ranking) on Step 6.
- **Animated reveal** on Step 2 (county-by-county fill transition).
- **Button-triggered playback** on Step 0 with Replay.
- **Hover tooltips** on every chart with country / county / value detail.
- **State drill-down** in the bubble view.
- **In-chart annotations** on every step so prose references resolve to specific marks.

---

## Slide 14 — Reflection (0:30)

- **What worked:** scrollytelling kept the argument sequenced; sticky charts gave each prose beat a visual anchor.
- **What we'd redo:** consider deck.gl 3D extruded county map as a Step 0 alternative — more striking, but harder to keep accessible.
- **Hardest part:** keeping the same 20-country roster visually consistent across Steps 4, 5, 6. The morph is what makes that roster legible.

---

## Slide 15 — Q&A / Links (0:15)

**Live demo:** https://57777-bit.github.io/5609finalProject/
**Repo:** https://github.com/57777-bit/5609finalProject

**Acknowledgements**
- Chetty et al., *The Opportunity Atlas* — opportunityatlas.org
- World Bank GDIM 2023 · Frederick Solt's SWIID v9.6
- Mike Bostock's TopoJSON Atlas · D3 · Svelte / SvelteKit

---

## Suggested Demo Path (if live demo time-boxed to 90s)

1. Land on hero, hit **Play** → watch tier animation (~10s).
2. Click any state in the Dorling bubble view → zoom into that state's counties (~10s).
3. Scroll through Steps 1 → 5 quickly (~30s) to show prose+chart binding.
4. Stop on Step 6 → wait for the morph from scatter to bars (~15s).
5. Hover on the U.S. row to show tooltip (~5s).
6. Quick scroll back up to show stickiness still works (~15s).

## Backup Demo Plan (if live URL is down)

Use a screen recording of the same path. Keep one in the deck on the second-to-last slide as a hidden backup.

---

## Time Budget Summary

| Section | Time |
|---|---|
| Title + Question | 1:00 |
| Data + Tech | 1:00 |
| Steps 0–3 walkthrough | 2:00 |
| Steps 4–6 walkthrough (with morph) | 2:30 |
| Design decisions + reflection | 1:15 |
| Q&A buffer | 0:15 |
| **Total** | **8:00 max** |

If the slot is 5 minutes, drop Steps 1–3 narration and let the demo carry them.

# The Geography of Opportunity

An interactive scrollytelling visualization exploring the geographic determinants of economic mobility in the United States, and how the U.S. compares against other wealthy economies on the same metric.

**CSCI 5609 — Final Project**

---

## Project Question

> How much does where an American child grows up shape their adult economic outcomes — and how does the U.S. as a whole compare against its wealthy peers?

The piece is structured as a two-act narrative:

- **Part I — The American Problem.** Within the United States, mobility is sharply geographic. The same generation, born in the same country, experiences profoundly different chances of rising depending only on the county they were born in.
- **Part II — The Global Perspective.** Stepping back, the U.S. as a whole sits below most of its wealthy peer economies on intergenerational mobility. Birthplace is not destiny: countries with comparable means achieve more mobility through different choices in schools, taxation, and family supports.

---

## Visualizations

The story uses seven coordinated visualizations on the right panel, each linked to scroll-driven narrative on the left.

| # | Component | Purpose |
|---|---|---|
| 1 | `Scrollymap` | County-level choropleth of U.S. mobility outcomes; toggles between county view and state-bubble view; supports state click-to-zoom |
| 2 | `ScatterPlot` | Poor-children vs rich-children adult-rank comparison by county |
| 3 | `ChangeMap` | County-level change in mobility outcomes between cohorts |
| 4 | `SchoolFunding` | Bridge visualization linking education spending to mobility outcomes |
| 5 | `MobilityGap` | Bubble chart of cross-country mobility gaps |
| 6 | `RedistributionDumbbell` | Pre-tax vs post-tax inequality across countries (dumbbell plot) |
| 7 | `MobilityLeague` | Ranking of major economies by intergenerational immobility (IGE), with the U.S. highlighted in red and named peer economies in deep blue |

All visualizations are implemented in D3 v7 with Albers USA projections for U.S. maps and TopoJSON for boundary data.

---

## Interactivity

- **Button-triggered animation.** The opening county map auto-plays through three mobility tiers (stuck → treading water → climbing) on user click, rather than scroll-trigger, to ensure layout stability on fast scrolls.
- **Scroll-driven narrative.** Beyond the opening, the right panel transitions through six chart steps as the user scrolls.
- **Tab toggle.** The county map can be switched into a state-bubble aggregation.
- **State drill-down.** Clicking any state in the bubble view zooms into its constituent counties.
- **Replay.** After auto-play completes, a Replay button restores the animation.
- **Inline annotations.** Key data points (e.g., the U.S. rank in the league table, named peer rows) are annotated directly on the chart so prose references resolve to specific marks.

---

## Datasets

All datasets are public and include in `static/data/`:

| File | Source | Use |
|---|---|---|
| `counties-10m.json` | US Census via TopoJSON Atlas | County and state boundaries |
| `data.json` | Opportunity Atlas (Chetty et al.) — county-level adult outcomes by parent income | County mobility maps and ScatterPlot |
| `school_funding.csv` | U.S. Department of Education school finance data | School funding visualization |
| `GDIM_2023_03.csv` | Global Database of Intergenerational Mobility (World Bank) 2023 release | International IGE comparisons |
| `swiid9_6_summary.csv` | Standardized World Income Inequality Database v9.6 (Solt) | Pre- and post-tax Gini for the redistribution dumbbell |

Data filtering and preparation:

- `MobilityLeague` filters GDIM rows to `parent=avg, child=all` and averages multiple BETA estimates per country, then restricts the league to a curated set of 20 major economies for narrative coherence.
- `RedistributionDumbbell` uses SWIID v9.6 summary records and pairs market-Gini with disposable-Gini per country.
- County data is rendered against the 10-million-vertex Albers USA TopoJSON; Alaska/Hawaii are repositioned by the projection.

---

## Tech Stack

- **SvelteKit** with **Svelte 5 runes** (`$state`, `$bindable`, `$props`, `$effect`)
- **D3 v7** for scales, axes, projections, and selections
- **topojson-client** for boundary tessellation
- **Vite** dev server with HMR
- **TypeScript** for config and type-checked entry points

No backend; the entire site is statically rendered/exported.

---

## Running Locally

```bash
npm install
npm run dev          # opens http://localhost:5173
```

Build a static production bundle:

```bash
npm run build
npm run preview      # preview the production bundle
```

Type-check without running:

```bash
npm run check
```

---

## Project Layout

```
src/
├── routes/
│   └── +page.svelte         # Main scrollytelling page: hero, 7 steps, footer
├── components/
│   ├── Scrollymap.svelte    # Step 0: county/state mobility map
│   ├── ScatterPlot.svelte   # Step 1: poor vs rich county scatter
│   ├── ChangeMap.svelte     # Step 2: cohort-to-cohort change map
│   ├── SchoolFunding.svelte # Step 3: school funding bridge
│   ├── MobilityGap.svelte   # Step 4: cross-country gap bubbles
│   ├── RedistributionDumbbell.svelte  # Step 5: pre/post tax dumbbell
│   └── MobilityLeague.svelte          # Step 6: country IGE league table
static/
└── data/                    # All datasets
```

---

## Design Decisions

- **Two-act structure** (American problem → global perspective). The local-then-global pivot lets the reader internalize the within-country geographic spread before being asked to weigh the U.S. against peers.
- **Sticky right panel** with scrollytelling left panel. The chart stays anchored as the prose advances, so each narrative beat resolves against a visible mark.
- **Word-image binding.** When the prose names a country, that country's row is visibly distinguished on the chart (deep-blue label, bold weight, deep-blue bar, and a `▸ peer` tag). When the prose names the U.S., the U.S. bar carries an inline rank callout (`U.S. — rank 10 of 20`).
- **Curated league roster.** Rather than including outlier low-IGE microstates (Mauritius, Maldives, etc.), the league is restricted to 20 major economies so the "rich peer comparison" framing in the prose has a visually coherent roster.
- **Button trigger over scroll trigger** for the opening animation. Scroll triggers were producing layout reflow races on fast scrolls; an explicit Play button locks the section to 100vh and removes that class of bug.

---

## Team and Contributions

| Member | Contributions |
|---|---|
| Brandon Borzello | Visualizations & animations · Presentation · Project leadership |
| Harris Li | Visualizations & animations · Supporting datasets |
| Qi Wu | Site scaffolding · Visualizations & animations · Primary datasets · Project leadership |
| Yiqi Huang | Visualizations & animations · Primary datasets · Presentation · Project leadership |

---

## Attributions and Acknowledgements

- County mobility data: Chetty et al., *The Opportunity Atlas* — https://www.opportunityatlas.org
- GDIM 2023: World Bank Group, *Global Database on Intergenerational Mobility* (2023 release)
- SWIID v9.6: Frederick Solt, *The Standardized World Income Inequality Database*
- US boundary TopoJSON: TopoJSON Atlas (Mike Bostock)
- D3.js: Mike Bostock and contributors
- Svelte and SvelteKit: Rich Harris and contributors

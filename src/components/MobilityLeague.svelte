<script>
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';

  let svgEl = $state(null);
  let rows = $state([]);
  let hasMorphed = $state(false);

  // Wealthy peer economies named in the prose ("Canada, Sweden, the United
  // Kingdom, Japan") — give them a distinct deep-blue accent so the four
  // bolded names in the footer text resolve to four visibly emphasised rows.
  const PEERS = new Set(['Canada', 'Sweden', 'United Kingdom', 'Japan']);
  const PEER_COLOR = '#1F4E79';
  const US_COLOR = '#C0392B';
  const DEFAULT_COLOR = '#5DADE2';

  async function loadData() {
    const [gdimRows, swiidRows] = await Promise.all([
      d3.csv(`${base}/data/GDIM_2023_03.csv`),
      d3.csv(`${base}/data/swiid9_6_summary.csv`)
    ]);

    const grouped = new Map();
    for (const r of gdimRows) {
      if (r.parent !== 'avg' || r.child !== 'all') continue;
      const beta = Number(r.BETA);
      if (!Number.isFinite(beta)) continue;
      const arr = grouped.get(r.country) ?? [];
      arr.push(beta);
      grouped.set(r.country, arr);
    }

    // Latest-year Gini per country, used to seed the scatter form before
    // the chart morphs into bars. Keeping the scatter coords here means
    // the same set of countries shown in Step 4 (Great Gatsby Curve)
    // visibly carries over into Step 6 instead of appearing from nowhere.
    const giniByCountry = new Map();
    for (const r of swiidRows) {
      const year = Number(r.year);
      const gini = Number(r.gini_disp);
      if (!Number.isFinite(year) || !Number.isFinite(gini)) continue;
      const prev = giniByCountry.get(r.country);
      if (!prev || year > prev.year) {
        giniByCountry.set(r.country, { year, gini });
      }
    }

    const all = [...grouped.entries()].map(([country, vals]) => ({
      country,
      ige: d3.mean(vals)
    })).sort((a, b) => a.ige - b.ige);

    // Curated league: focus on rich peer economies + a few high-inequality
    // reference points. The footer prose talks about "rich peer economies"
    // so the chart's roster needs to read as such — random low-IGE outliers
    // (Mauritius, Uzbekistan, Maldives, etc.) muddied the visual story.
    const KEEP = new Set([
      'United States',
      'Canada', 'Sweden', 'United Kingdom', 'Japan',
      'Germany', 'France', 'Italy', 'Denmark', 'Norway',
      'Netherlands', 'Australia', 'Spain', 'Finland', 'Belgium',
      'Switzerland', 'Korea, Rep.',
      'China', 'Brazil', 'India',
    ]);

    rows = all
      .filter((d) => KEEP.has(d.country))
      .map((d) => ({
        ...d,
        gini: giniByCountry.get(d.country)?.gini ?? null
      }))
      .sort((a, b) => a.ige - b.ige);
  }

  function fillFor(country) {
    if (country === 'United States') return US_COLOR;
    if (PEERS.has(country)) return PEER_COLOR;
    return DEFAULT_COLOR;
  }

  function opacityFor(country) {
    if (country === 'United States') return 0.95;
    if (PEERS.has(country)) return 0.85;
    return 0.70;
  }

  function draw() {
    if (!svgEl || rows.length === 0) return;

    const W = svgEl.clientWidth || 760;
    const H = Math.max(460, Math.round(W * 0.58));
    const margin = { top: 28, right: 24, bottom: 50, left: 170 };
    const innerW = W - margin.left - margin.right;
    const innerH = H - margin.top - margin.bottom;

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // Bar scales (final state).
    const xBar = d3.scaleLinear()
      .domain(d3.extent(rows, (d) => d.ige))
      .nice()
      .range([0, innerW]);

    const yBar = d3.scaleBand()
      .domain(rows.map((d) => d.country))
      .range([0, innerH])
      .padding(0.30);

    // Scatter scales (initial morph-from state). The y axis is shared in
    // spirit (IGE) but we use a finer-resolution scatter Y so dots don't
    // collapse onto identical rows.
    const xScatter = d3.scaleLinear()
      .domain(d3.extent(rows.filter((d) => d.gini != null), (d) => d.gini))
      .nice()
      .range([Math.round(innerW * 0.10), Math.round(innerW * 0.90)]);

    const yScatter = d3.scaleLinear()
      .domain(d3.extent(rows, (d) => d.ige))
      .nice()
      .range([innerH - 20, 20]);

    const dotR = 8;

    // Marks: rect-with-rx, used for both forms. Initial form has square
    // dimensions and full rx so they read as circles; the morph stretches
    // them horizontally and squashes rx so they read as bars.
    const marks = g.selectAll('rect.mark')
      .data(rows, (d) => d.country)
      .join('rect')
      .attr('class', 'mark')
      .attr('x', (d) => d.gini != null ? xScatter(d.gini) - dotR : -dotR * 4)
      .attr('y', (d) => yScatter(d.ige) - dotR)
      .attr('width', dotR * 2)
      .attr('height', dotR * 2)
      .attr('rx', dotR)
      .attr('fill', (d) => fillFor(d.country))
      .attr('opacity', (d) => d.country === 'United States' ? 0.95 : 0.80);

    // "Initial scatter view" hint label, fades out before morph.
    const hintLabel = g.append('text')
      .attr('x', innerW / 2)
      .attr('y', innerH + 36)
      .attr('text-anchor', 'middle')
      .attr('font-size', 11)
      .attr('font-weight', 600)
      .attr('fill', '#888')
      .attr('opacity', 0)
      .text('Same 20 countries from the Great Gatsby curve — now ranking them');

    hintLabel.transition().duration(350).attr('opacity', 1);

    // Stage 1 → morph rect into bar form.
    const morphDelay = 1100;
    const morphDuration = 1200;

    marks.transition()
      .delay(morphDelay)
      .duration(morphDuration)
      .ease(d3.easeCubicInOut)
      .attr('x', 0)
      .attr('y', (d) => yBar(d.country))
      .attr('width', (d) => xBar(d.ige))
      .attr('height', yBar.bandwidth())
      .attr('rx', 2)
      .attr('opacity', (d) => opacityFor(d.country));

    // Stage 1 → fade out the hint label as the morph begins.
    hintLabel.transition()
      .delay(morphDelay - 100)
      .duration(300)
      .attr('opacity', 0)
      .remove();

    // Stage 2 → axes, labels, callouts appear after morph completes.
    const decorDelay = morphDelay + morphDuration - 200;
    const decorGroup = g.append('g').attr('class', 'decor').attr('opacity', 0);

    decorGroup.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(xBar).ticks(6))
      .call((gg) => gg.select('.domain').attr('stroke', '#bbb'))
      .call((gg) => gg.selectAll('text').attr('fill', '#6a6a6a').attr('font-size', 11));

    decorGroup.append('g')
      .call(d3.axisLeft(yBar).tickSize(0))
      .call((gg) => gg.select('.domain').remove())
      .call((gg) => gg.selectAll('text')
        .attr('fill', (d) => {
          if (d === 'United States') return US_COLOR;
          if (PEERS.has(d)) return PEER_COLOR;
          return '#4b4b4b';
        })
        .attr('font-weight', (d) => (d === 'United States' || PEERS.has(d)) ? '700' : '500')
        .attr('font-size', 11));

    decorGroup.append('line')
      .attr('x1', xBar(d3.mean(rows, (d) => d.ige)))
      .attr('x2', xBar(d3.mean(rows, (d) => d.ige)))
      .attr('y1', 0)
      .attr('y2', innerH)
      .attr('stroke', '#c9c9c9')
      .attr('stroke-dasharray', '5,4');

    // U.S. rank callout.
    const usIdx = rows.findIndex((r) => r.country === 'United States');
    if (usIdx >= 0) {
      const us = rows[usIdx];
      decorGroup.append('text')
        .attr('x', xBar(us.ige) + 6)
        .attr('y', yBar(us.country) + yBar.bandwidth() / 2 + 4)
        .attr('font-size', 11)
        .attr('font-weight', 700)
        .attr('fill', US_COLOR)
        .text(`U.S. — rank ${usIdx + 1} of ${rows.length}`);
    }

    // Peer tags on the four named peer economies.
    const peerRows = rows.filter((r) => PEERS.has(r.country));
    decorGroup.selectAll('text.peer-tag')
      .data(peerRows)
      .join('text')
      .attr('class', 'peer-tag')
      .attr('x', (d) => xBar(d.ige) + 6)
      .attr('y', (d) => yBar(d.country) + yBar.bandwidth() / 2 + 4)
      .attr('font-size', 10)
      .attr('font-weight', 700)
      .attr('fill', PEER_COLOR)
      .text('▸ peer');

    decorGroup.append('text')
      .attr('x', innerW / 2)
      .attr('y', innerH + 38)
      .attr('text-anchor', 'middle')
      .attr('font-size', 12)
      .attr('font-weight', '600')
      .attr('fill', '#555')
      .text('Intergenerational immobility (IGE, lower = more mobile)');

    // In-chart takeaway annotation: short headline + leader to U.S. bar.
    if (usIdx >= 0) {
      const us = rows[usIdx];
      const annoX = innerW * 0.55;
      const annoY = 14;
      const annoG = decorGroup.append('g').attr('class', 'takeaway-anno');
      annoG.append('text')
        .attr('x', annoX)
        .attr('y', annoY)
        .attr('font-size', 12)
        .attr('font-weight', 700)
        .attr('fill', '#2c3e50')
        .text('Nine wealthy peers rank above the U.S.');
      annoG.append('line')
        .attr('x1', annoX)
        .attr('y1', annoY + 6)
        .attr('x2', xBar(us.ige) + 4)
        .attr('y2', yBar(us.country) + yBar.bandwidth() / 2)
        .attr('stroke', '#888')
        .attr('stroke-width', 1)
        .attr('stroke-dasharray', '3,3');
    }

    decorGroup.transition()
      .delay(decorDelay)
      .duration(450)
      .attr('opacity', 1)
      .on('end', () => { hasMorphed = true; });
  }

  onMount(async () => {
    await loadData();
    draw();
    const ro = new ResizeObserver(() => draw());
    ro.observe(svgEl);
    return () => ro.disconnect();
  });
</script>

<div class="chart-wrapper">
  <h3>Mobility League Table</h3>
  <p class="subtitle">Watch the same countries from the Gatsby curve regroup into a ranking. Lower IGE means higher mobility. The U.S. is highlighted in red.</p>

  <div class="how-to-read">
    <span class="htr-label">How to read</span>
    <ul>
      <li><strong>Bar length — IGE β:</strong> calculated as the slope of an OLS regression of log(child income) on log(parent income) — captures what fraction of a parent's income advantage is passed to their child.</li>
      <li><strong>Shorter bar = more mobile</strong> — a 1% higher parent income predicts little change in child income; children can climb regardless of birth.</li>
      <li><strong>Longer bar = more stuck</strong> — income advantage reliably passes down; the regression slope is steep.</li>
    </ul>
  </div>

  <svg bind:this={svgEl} style="width:100%;display:block;"></svg>
  <div class="source">Source: GDIM 2023 (parent=avg, child=all) · SWIID v9.6 (latest year, for the opening scatter positions)</div>
</div>

<style>
  .chart-wrapper {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.07);
    padding: 16px;
    box-sizing: border-box;
  }
  h3 { margin: 0; font-size: 1.15rem; color: #2c3e50; }
  .subtitle { margin: 4px 0 6px; font-size: 0.84rem; color: #7b8a8b; }

  .how-to-read {
    background: #f0f4f8;
    border-left: 3px solid #2471A3;
    border-radius: 0 6px 6px 0;
    padding: 7px 12px;
    margin-bottom: 8px;
    font-size: 0.76rem;
    color: #4a5568;
    line-height: 1.5;
  }

  .htr-label {
    display: block;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.67rem;
    color: #2471A3;
    margin-bottom: 4px;
  }

  .how-to-read ul {
    margin: 0;
    padding-left: 14px;
  }

  .how-to-read li { margin: 2px 0; }

  .source {
    border-top: 1px solid #ecf0f1;
    margin-top: 8px;
    padding-top: 8px;
    font-size: 0.75rem;
    color: #9aa0a6;
    text-align: right;
  }
</style>

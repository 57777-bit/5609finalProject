<script>
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';

  let svgEl = $state(null);
  let rows = $state([]);

  // Wealthy peer economies named in the prose ("Canada, Sweden, the United
  // Kingdom, Japan") — give them a distinct deep-blue accent so the four
  // bolded names in the footer text resolve to four visibly emphasised rows.
  const PEERS = new Set(['Canada', 'Sweden', 'United Kingdom', 'Japan']);
  const PEER_COLOR = '#1F4E79';

  async function loadData() {
    const gdimRows = await d3.csv(`${base}/data/GDIM_2023_03.csv`);

    const grouped = new Map();
    for (const r of gdimRows) {
      if (r.parent !== 'avg' || r.child !== 'all') continue;
      const beta = Number(r.BETA);
      if (!Number.isFinite(beta)) continue;
      const arr = grouped.get(r.country) ?? [];
      arr.push(beta);
      grouped.set(r.country, arr);
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
      // Named peers (highlighted in deep blue)
      'Canada', 'Sweden', 'United Kingdom', 'Japan',
      // Other major rich economies
      'Germany', 'France', 'Italy', 'Denmark', 'Norway',
      'Netherlands', 'Australia', 'Spain', 'Finland', 'Belgium',
      'Switzerland', 'Korea, Rep.',
      // Reference points for context (large/high-inequality economies)
      'China', 'Brazil', 'India',
    ]);

    rows = all
      .filter((d) => KEEP.has(d.country))
      .sort((a, b) => a.ige - b.ige);
  }

  function draw() {
    if (!svgEl || rows.length === 0) return;

    const W = svgEl.clientWidth || 760;
    const H = Math.max(460, Math.round(W * 0.58));
    const margin = { top: 24, right: 20, bottom: 44, left: 170 };
    const innerW = W - margin.left - margin.right;
    const innerH = H - margin.top - margin.bottom;

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear()
      .domain(d3.extent(rows, (d) => d.ige))
      .nice()
      .range([0, innerW]);

    const y = d3.scaleBand()
      .domain(rows.map((d) => d.country))
      .range([0, innerH])
      .padding(0.28);

    g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6))
      .call((gg) => gg.select('.domain').attr('stroke', '#bbb'))
      .call((gg) => gg.selectAll('text').attr('fill', '#6a6a6a').attr('font-size', 11));

    g.append('g')
      .call(d3.axisLeft(y).tickSize(0))
      .call((gg) => gg.select('.domain').remove())
      .call((gg) => gg.selectAll('text')
        .attr('fill', (d) => {
          if (d === 'United States') return '#C0392B';
          if (PEERS.has(d)) return PEER_COLOR;
          return '#4b4b4b';
        })
        .attr('font-weight', (d) => (d === 'United States' || PEERS.has(d)) ? '700' : '500')
        .attr('font-size', 11));

    g.append('line')
      .attr('x1', x(d3.mean(rows, (d) => d.ige)))
      .attr('x2', x(d3.mean(rows, (d) => d.ige)))
      .attr('y1', 0)
      .attr('y2', innerH)
      .attr('stroke', '#c9c9c9')
      .attr('stroke-dasharray', '5,4');

    g.selectAll('rect.bar')
      .data(rows)
      .join('rect')
      .attr('class', 'bar')
      .attr('x', 0)
      .attr('y', (d) => y(d.country))
      .attr('width', (d) => x(d.ige))
      .attr('height', y.bandwidth())
      .attr('rx', 2)
      .attr('fill', (d) => {
        if (d.country === 'United States') return '#C0392B';
        if (PEERS.has(d.country)) return PEER_COLOR;
        return '#5DADE2';
      })
      .attr('opacity', (d) => {
        if (d.country === 'United States') return 0.95;
        if (PEERS.has(d.country)) return 0.85;
        return 0.65;
      });

    // Inline rank callout for the U.S. bar so "near the bottom" in prose
    // resolves to a concrete position number on the chart.
    const usIdx = rows.findIndex((r) => r.country === 'United States');
    if (usIdx >= 0) {
      const us = rows[usIdx];
      g.append('text')
        .attr('x', x(us.ige) + 6)
        .attr('y', y(us.country) + y.bandwidth() / 2 + 4)
        .attr('font-size', 11)
        .attr('font-weight', 700)
        .attr('fill', '#C0392B')
        .text(`U.S. — rank ${usIdx + 1} of ${rows.length}`);
    }

    // Small "peer" tags on the four named peer economies so the four bolded
    // names in the footer text have a 1:1 visual anchor on the chart.
    const peerRows = rows.filter((r) => PEERS.has(r.country));
    g.selectAll('text.peer-tag')
      .data(peerRows)
      .join('text')
      .attr('class', 'peer-tag')
      .attr('x', (d) => x(d.ige) + 6)
      .attr('y', (d) => y(d.country) + y.bandwidth() / 2 + 4)
      .attr('font-size', 10)
      .attr('font-weight', 700)
      .attr('fill', PEER_COLOR)
      .text('▸ peer');

    g.append('text')
      .attr('x', innerW / 2)
      .attr('y', innerH + 36)
      .attr('text-anchor', 'middle')
      .attr('font-size', 12)
      .attr('font-weight', '600')
      .attr('fill', '#555')
      .text('Intergenerational immobility (IGE, lower = more mobile)');
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
  <p class="subtitle">Lower IGE means higher mobility. The U.S. is highlighted in red.</p>
  <svg bind:this={svgEl} style="width:100%;display:block;"></svg>
  <div class="source">Source: GDIM 2023 (parent=avg, child=all)</div>
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
  .subtitle { margin: 4px 0 8px; font-size: 0.84rem; color: #7b8a8b; }
  .source {
    border-top: 1px solid #ecf0f1;
    margin-top: 8px;
    padding-top: 8px;
    font-size: 0.75rem;
    color: #9aa0a6;
    text-align: right;
  }
</style>

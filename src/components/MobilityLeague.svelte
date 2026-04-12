<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';

  let svgEl = $state(null);
  let rows = $state([]);

  async function loadData() {
    const gdimRows = await d3.csv('/data/GDIM_2023_03.csv');

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

    const keep = new Set(['United States', 'United Kingdom', 'Canada', 'Germany', 'Japan', 'China', 'Brazil', 'Denmark', 'Sweden']);
    const top = all.slice(0, 8);
    const bottom = all.slice(-8);

    rows = [...top, ...bottom, ...all.filter((d) => keep.has(d.country))]
      .filter((d, i, arr) => arr.findIndex((x) => x.country === d.country) === i)
      .sort((a, b) => a.ige - b.ige)
      .slice(0, 20);
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
        .attr('fill', (d) => d === 'United States' ? '#C0392B' : '#4b4b4b')
        .attr('font-weight', (d) => d === 'United States' ? '700' : '500')
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
      .attr('fill', (d) => d.country === 'United States' ? '#C0392B' : '#5DADE2')
      .attr('opacity', (d) => d.country === 'United States' ? 0.95 : 0.72);

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

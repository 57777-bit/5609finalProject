<script>
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';

  let svgEl = $state(null);
  let rows = $state([]);
  let tooltip = $state({ visible: false, x: 0, y: 0, country: '', market: 0, disp: 0, red: 0 });

  // Nordic countries get a green accent so the prose mention of "Nordic" / "20+ pts"
  // resolves visually to specific lines on the dumbbell.
  const NORDIC = new Set(['Sweden', 'Denmark', 'Norway', 'Finland', 'Iceland']);
  const NORDIC_COLOR = '#27AE60';

  async function loadData() {
    const [gdimRows, swiidRows] = await Promise.all([
      d3.csv(`${base}/data/GDIM_2023_03.csv`),
      d3.csv(`${base}/data/swiid9_6_summary.csv`)
    ]);

    const gdimCountries = new Set();
    for (const r of gdimRows) {
      if (r.parent === 'avg' && r.child === 'all' && Number.isFinite(Number(r.BETA))) {
        gdimCountries.add(r.country);
      }
    }

    const latest = new Map();
    for (const r of swiidRows) {
      if (!gdimCountries.has(r.country)) continue;

      const year = Number(r.year);
      const giniDisp = Number(r.gini_disp);
      const giniMkt = Number(r.gini_mkt);
      let absRed = Number(r.abs_red);

      if (!Number.isFinite(year) || !Number.isFinite(giniDisp) || !Number.isFinite(giniMkt)) continue;
      if (!Number.isFinite(absRed)) absRed = giniMkt - giniDisp;
      if (!Number.isFinite(absRed)) continue;

      const prev = latest.get(r.country);
      if (!prev || year > prev.year) {
        latest.set(r.country, {
          country: r.country,
          year,
          gini_mkt: giniMkt,
          gini_disp: giniDisp,
          abs_red: absRed
        });
      }
    }

    const all = [...latest.values()].sort((a, b) => b.abs_red - a.abs_red);
    const spotlight = new Set(['United States', 'United Kingdom', 'Canada', 'Germany', 'Sweden', 'Denmark']);

    const picked = [];
    for (const d of all) {
      if (picked.length >= 14) break;
      if (spotlight.has(d.country)) {
        picked.push(d);
      }
    }
    for (const d of all) {
      if (picked.length >= 14) break;
      if (!picked.find((x) => x.country === d.country)) {
        picked.push(d);
      }
    }

    rows = picked.sort((a, b) => b.abs_red - a.abs_red);
  }

  function draw() {
    if (!svgEl || rows.length === 0) return;

    const W = svgEl.clientWidth || 760;
    const H = Math.max(460, Math.round(W * 0.62));
    const margin = { top: 30, right: 24, bottom: 50, left: 180 };
    const innerW = W - margin.left - margin.right;
    const innerH = H - margin.top - margin.bottom;

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const xMin = d3.min(rows, (d) => d.gini_disp) - 2;
    const xMax = d3.max(rows, (d) => d.gini_mkt) + 2;

    const x = d3.scaleLinear().domain([xMin, xMax]).range([0, innerW]);
    const y = d3.scaleBand().domain(rows.map((d) => d.country)).range([0, innerH]).padding(0.35);

    g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6).tickSize(-innerH).tickFormat(''))
      .call((gg) => gg.select('.domain').remove())
      .call((gg) => gg.selectAll('line').attr('stroke', '#ececec'));

    g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6))
      .call((gg) => gg.select('.domain').attr('stroke', '#bbb'))
      .call((gg) => gg.selectAll('text').attr('fill', '#6b6b6b').attr('font-size', 11));

    g.append('g')
      .call(d3.axisLeft(y).tickSize(0))
      .call((gg) => gg.select('.domain').remove())
      .call((gg) => gg.selectAll('text')
        .attr('fill', (d) => {
          if (d === 'United States') return '#C0392B';
          if (NORDIC.has(d)) return NORDIC_COLOR;
          return '#4a4a4a';
        })
        .attr('font-weight', (d) => (d === 'United States' || NORDIC.has(d)) ? '700' : '500')
        .attr('font-size', 11));

    g.selectAll('line.link')
      .data(rows)
      .join('line')
      .attr('class', 'link')
      .attr('x1', (d) => x(d.gini_disp))
      .attr('x2', (d) => x(d.gini_mkt))
      .attr('y1', (d) => y(d.country) + y.bandwidth() / 2)
      .attr('y2', (d) => y(d.country) + y.bandwidth() / 2)
      .attr('stroke', (d) => NORDIC.has(d.country) ? NORDIC_COLOR : '#c7c7c7')
      .attr('stroke-width', (d) => NORDIC.has(d.country) ? 3 : 2)
      .attr('opacity', (d) => NORDIC.has(d.country) ? 0.85 : 1);

    const dot = (cls, accessor, color) => g.selectAll(`circle.${cls}`)
      .data(rows)
      .join('circle')
      .attr('class', cls)
      .attr('cx', (d) => x(accessor(d)))
      .attr('cy', (d) => y(d.country) + y.bandwidth() / 2)
      .attr('r', 4.6)
      .attr('fill', (d) => d.country === 'United States' ? '#C0392B' : color)
      .attr('opacity', 0.9)
      .on('mouseenter', function(ev, d) {
        const rect = svgEl.getBoundingClientRect();
        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 10,
          y: ev.clientY - rect.top - 14,
          country: d.country,
          market: d.gini_mkt,
          disp: d.gini_disp,
          red: d.abs_red
        };
        d3.select(this).attr('stroke', '#222').attr('stroke-width', 1.4);
      })
      .on('mousemove', function(ev) {
        const rect = svgEl.getBoundingClientRect();
        tooltip = { ...tooltip, x: ev.clientX - rect.left + 10, y: ev.clientY - rect.top - 14 };
      })
      .on('mouseleave', function() {
        tooltip = { ...tooltip, visible: false };
        d3.select(this).attr('stroke', null);
      });

    dot('disp', (d) => d.gini_disp, '#2E86C1');
    dot('mkt', (d) => d.gini_mkt, '#E67E22');

    g.append('text')
      .attr('x', innerW / 2)
      .attr('y', innerH + 40)
      .attr('text-anchor', 'middle')
      .attr('font-size', 12)
      .attr('fill', '#555')
      .attr('font-weight', '600')
      .text('Gini (market income to disposable income after taxes/transfers)');

    // Per-row "−N pts" labels on Nordic + U.S. rows so the prose mention of
    // "20+ points" / "barely moves the needle" resolves to actual line lengths.
    const annotated = rows.filter((d) => NORDIC.has(d.country) || d.country === 'United States');
    g.selectAll('text.red-callout')
      .data(annotated)
      .join('text')
      .attr('class', 'red-callout')
      .attr('x', (d) => x(d.gini_disp) - 8)
      .attr('y', (d) => y(d.country) + y.bandwidth() / 2 + 4)
      .attr('text-anchor', 'end')
      .attr('font-size', 10)
      .attr('font-weight', 700)
      .attr('fill', (d) => d.country === 'United States' ? '#C0392B' : NORDIC_COLOR)
      .text((d) => `−${d.abs_red.toFixed(1)} pts`);

    // Takeaway annotation comparing U.S. vs the strongest Nordic redistributor —
    // anchors the prose claim "U.S. barely moves the needle" to a specific gap.
    const usRow = rows.find((d) => d.country === 'United States');
    const topNordic = rows.filter((d) => NORDIC.has(d.country))
      .sort((a, b) => b.abs_red - a.abs_red)[0];
    if (usRow && topNordic) {
      const headlineY = -8;
      g.append('text')
        .attr('x', innerW)
        .attr('y', headlineY)
        .attr('text-anchor', 'end')
        .attr('font-size', 12)
        .attr('font-weight', 700)
        .attr('fill', '#2c3e50')
        .text(`U.S. cuts inequality by only ${usRow.abs_red.toFixed(1)} pts vs. ${topNordic.country}'s ${topNordic.abs_red.toFixed(1)} pts`);
    }
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
  <h3>Redistribution Dumbbell</h3>
  <p class="subtitle">How far each country moves from market inequality to disposable inequality.</p>

  <div class="how-to-read">
    <span class="htr-label">How to read</span>
    <ul>
      <li><strong>Orange dot (right) — Market Gini:</strong> Lorenz curve applied to pre-tax, pre-transfer income — raw labor market inequality before any government intervention.</li>
      <li><strong>Blue dot (left) — Disposable Gini:</strong> same Lorenz curve method applied to post-tax, post-transfer income — what families actually take home.</li>
      <li><strong>Line length</strong> = Market Gini − Disposable Gini = the redistribution effect. Longer = stronger policy intervention. Sorted by largest reduction.</li>
    </ul>
  </div>

  <div class="svg-wrap">
    <svg bind:this={svgEl} style="width:100%;display:block;"></svg>

    {#if tooltip.visible}
      <div class="tooltip" style="left:{tooltip.x}px;top:{tooltip.y}px">
        <div><strong>{tooltip.country}</strong></div>
        <div>Market Gini: {tooltip.market.toFixed(1)}</div>
        <div>Disposable Gini: {tooltip.disp.toFixed(1)}</div>
        <div>Reduction: -{tooltip.red.toFixed(1)} pts</div>
      </div>
    {/if}
  </div>

  <div class="legend-row">
    <span><span class="dot disp"></span>Disposable Gini</span>
    <span><span class="dot mkt"></span>Market Gini</span>
    <span class="source">Source: SWIID v9.6 summary + GDIM 2023 overlap</span>
  </div>
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

  .svg-wrap { position: relative; flex-grow: 1; min-height: 0; }
  .tooltip {
    position: absolute;
    background: rgba(20,20,24,0.95);
    color: #fff;
    padding: 8px 10px;
    border-radius: 8px;
    font-size: 12px;
    line-height: 1.5;
    pointer-events: none;
    z-index: 10;
  }
  .legend-row {
    border-top: 1px solid #ecf0f1;
    margin-top: 8px;
    padding-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    font-size: 0.77rem;
    color: #4f5b66;
  }
  .dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 5px;
  }
  .dot.disp { background: #2E86C1; }
  .dot.mkt { background: #E67E22; }
  .source { margin-left: auto; color: #9aa0a6; }
</style>

<script>
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';

  let svgEl = $state(null);
  let data = $state([]);
  let tooltip = $state({ visible: false, x: 0, y: 0, country: '', ige: 0, gini: 0, absRed: 0, region: '' });

  // Sources: GDIM_2023_03 (mobility) + SWIID v9.6 summary (inequality/redistribution)
  const regionColor = {
    'High-income economies': '#2471A3',
    'Europe & Central Asia': '#1A8A5A',
    'East Asia & Pacific': '#8E44AD',
    'Latin America & Caribbean': '#E67E22',
    'Sub-Saharan Africa': '#8C564B',
    'Middle East & North Africa': '#E377C2',
    'South Asia': '#17BECF',
    'Unknown': '#7F8C8D'
  };

  const keyLabels = ['United States', 'Brazil', 'China', 'Japan', 'Germany', 'United Kingdom', 'Canada'];
  // Nordic countries get a green accent so the prose mention of "Nordic benchmarks"
  // resolves visually to the lower-left cluster of the chart.
  const nordicLabels = ['Norway', 'Sweden', 'Denmark', 'Finland', 'Iceland'];
  const usColor = '#C0392B';
  const nordicColor = '#27AE60';
  const usRadius = 10;
  const nordicRadius = 8;
  const keyRadiusBoost = 1.6;

  function colorForRegion(region) {
    return regionColor[region] ?? regionColor.Unknown;
  }

  async function loadMergedData() {
    const [gdimRows, swiidRows] = await Promise.all([
      d3.csv(`${base}/data/GDIM_2023_03.csv`),
      d3.csv(`${base}/data/swiid9_6_summary.csv`)
    ]);

    const betaByCountry = new Map();
    const regionByCountry = new Map();

    for (const row of gdimRows) {
      if (row.parent !== 'avg' || row.child !== 'all') continue;

      const beta = Number(row.BETA);
      if (!Number.isFinite(beta)) continue;

      const arr = betaByCountry.get(row.country) ?? [];
      arr.push(beta);
      betaByCountry.set(row.country, arr);

      if (!regionByCountry.has(row.country) && row.region) {
        regionByCountry.set(row.country, row.region);
      }
    }

    const meanByCountry = new Map();
    for (const [country, vals] of betaByCountry.entries()) {
      meanByCountry.set(country, d3.mean(vals));
    }

    const latestSwiid = new Map();
    for (const row of swiidRows) {
      const year = Number(row.year);
      const giniDisp = Number(row.gini_disp);
      const giniMkt = Number(row.gini_mkt);
      let absRed = Number(row.abs_red);

      if (!Number.isFinite(year) || !Number.isFinite(giniDisp)) continue;

      if (!Number.isFinite(absRed) && Number.isFinite(giniMkt)) {
        absRed = giniMkt - giniDisp;
      }
      if (!Number.isFinite(absRed)) continue;

      const prev = latestSwiid.get(row.country);
      if (!prev || year > prev.year) {
        latestSwiid.set(row.country, {
          year,
          gini_disp: giniDisp,
          abs_red: absRed
        });
      }
    }

    const intersection = [...meanByCountry.keys()].filter((country) => latestSwiid.has(country));

    data = intersection
      .map((country) => ({
        country,
        ige: meanByCountry.get(country),
        gini_disp: latestSwiid.get(country).gini_disp,
        abs_red: latestSwiid.get(country).abs_red,
        region: regionByCountry.get(country) ?? 'Unknown'
      }))
      .filter((d) => Number.isFinite(d.ige) && Number.isFinite(d.gini_disp) && Number.isFinite(d.abs_red))
      .sort((a, b) => a.gini_disp - b.gini_disp);
  }

  function drawChart() {
    if (!svgEl || data.length === 0) return;

    const W = svgEl.clientWidth || 700;
    const widthDrivenH = Math.round(W * 0.78);
    const wrapH = svgEl.parentElement?.clientHeight ?? 0;
    const H = wrapH > 0 ? Math.min(widthDrivenH, wrapH) : widthDrivenH;
    const margin = { top: 34, right: 22, bottom: 54, left: 68 };
    const innerW = W - margin.left - margin.right;
    const innerH = H - margin.top - margin.bottom;

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${W} ${H}`).attr('height', H).style('height', `${H}px`);

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    const xExtent = d3.extent(data, (d) => d.gini_disp);
    const yExtent = d3.extent(data, (d) => d.ige);
    const xPad = 1.5;
    const yPad = 0.03;

    const x = d3.scaleLinear()
      .domain([xExtent[0] - xPad, xExtent[1] + xPad])
      .range([0, innerW]);
    const y = d3.scaleLinear()
      .domain([Math.max(0.10, yExtent[0] - yPad), yExtent[1] + yPad])
      .range([innerH, 0]);

    const maxAbsRed = d3.max(data, (d) => d.abs_red) ?? 25;
    const r = d3.scaleSqrt().domain([0, maxAbsRed]).range([4.4, 6.6]);

    g.append('g').attr('class', 'grid')
      .call(d3.axisLeft(y).ticks(6).tickSize(-innerW).tickFormat(''))
      .call((gg) => gg.select('.domain').remove())
      .call((gg) => gg.selectAll('line').attr('stroke', '#e8e8e8').attr('stroke-dasharray', '3,3'));

    g.append('g').attr('class', 'grid')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(7).tickSize(-innerH).tickFormat(''))
      .call((gg) => gg.select('.domain').remove())
      .call((gg) => gg.selectAll('line').attr('stroke', '#e8e8e8').attr('stroke-dasharray', '3,3'));

    const xVals = data.map((d) => d.gini_disp);
    const yVals = data.map((d) => d.ige);
    const meanX = d3.mean(xVals);
    const meanY = d3.mean(yVals);
    const slope = d3.sum(data.map((d) => (d.gini_disp - meanX) * (d.ige - meanY))) /
                  d3.sum(data.map((d) => (d.gini_disp - meanX) ** 2));
    const intercept = meanY - slope * meanX;
    const trendX1 = x.domain()[0];
    const trendX2 = x.domain()[1];

    g.append('line')
      .attr('x1', x(trendX1)).attr('y1', y(slope * trendX1 + intercept))
      .attr('x2', x(trendX2)).attr('y2', y(slope * trendX2 + intercept))
      .attr('stroke', '#aaa').attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '6,4').attr('opacity', 0.7);

    g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(7))
      .call((gg) => gg.select('.domain').attr('stroke', '#ccc'))
      .call((gg) => gg.selectAll('text').attr('fill', '#777').attr('font-size', 11));

    g.append('g')
      .call(d3.axisLeft(y).ticks(6).tickFormat((d) => d.toFixed(2)))
      .call((gg) => gg.select('.domain').attr('stroke', '#ccc'))
      .call((gg) => gg.selectAll('text').attr('fill', '#777').attr('font-size', 11));

    g.append('text')
      .attr('x', innerW / 2).attr('y', innerH + 46)
      .attr('text-anchor', 'middle').attr('font-size', 12)
      .attr('fill', '#555').attr('font-weight', '600')
      .text('After-tax inequality (Gini, higher = more unequal)');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerH / 2).attr('y', -42)
      .attr('text-anchor', 'middle').attr('font-size', 12)
      .attr('fill', '#555').attr('font-weight', '600')
      .text('Immobility (IGE, higher = less mobile)');

    const dots = g.selectAll('circle.country-dot')
      .data(data)
      .join('circle')
      .attr('class', 'country-dot')
      .attr('cx', (d) => x(d.gini_disp))
      .attr('cy', (d) => y(d.ige))
      .attr('r', 0)
      .attr('fill', (d) => {
        if (d.country === 'United States') return usColor;
        if (nordicLabels.includes(d.country)) return nordicColor;
        return colorForRegion(d.region);
      })
      .attr('opacity', (d) => {
        if (d.country === 'United States') return 0.95;
        if (nordicLabels.includes(d.country)) return 0.92;
        return 0.58;
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', (d) => d.country === 'United States' ? 1.2 : 0.8)
      .style('cursor', 'pointer')
      .on('mouseenter', function(ev, d) {
        d3.select(this).raise().attr('stroke', '#333').attr('stroke-width', 1.4).attr('opacity', 1);
        const rect = svgEl.getBoundingClientRect();
        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 14,
          y: ev.clientY - rect.top - 14,
          country: d.country,
          ige: d.ige,
          gini: d.gini_disp,
          absRed: d.abs_red,
          region: d.region
        };
      })
      .on('mousemove', function(ev) {
        const rect = svgEl.getBoundingClientRect();
        tooltip = { ...tooltip, x: ev.clientX - rect.left + 14, y: ev.clientY - rect.top - 14 };
      })
      .on('mouseleave', function(ev, d) {
        d3.select(this).attr('stroke', '#fff').attr('stroke-width', 0.8)
          .attr('opacity', (keyLabels.includes(d.country) || nordicLabels.includes(d.country)) ? 0.92 : 0.58);
        tooltip = { ...tooltip, visible: false };
      });

    dots.transition().duration(600).delay((d, i) => i * 10)
      .attr('r', (d) => {
        const baseR = Math.max(4.4, r(d.abs_red));
        if (d.country === 'United States') return usRadius;
        if (nordicLabels.includes(d.country)) return nordicRadius;
        if (keyLabels.includes(d.country)) return baseR + keyRadiusBoost;
        return baseR;
      });

    const labelOffsets = {
      'United States':   { dx:   8, dy: -12 },
      'Brazil':          { dx:   8, dy:   5 },
      'China':           { dx:   8, dy: -10 },
      'Japan':           { dx: -36, dy:  14 },
      'Germany':         { dx:   8, dy:  -8 },
      'United Kingdom':  { dx:   8, dy: -10 },
      'Canada':          { dx:   8, dy:  14 },
      'Norway':          { dx: -42, dy:   4 },
      'Sweden':          { dx:   8, dy:  -8 },
      'Denmark':         { dx:   8, dy:  12 },
      'Finland':         { dx: -42, dy:  -6 },
      'Iceland':         { dx: -42, dy:  14 },
    };

    g.selectAll('text.country-label')
      .data(data.filter((d) => keyLabels.includes(d.country) || nordicLabels.includes(d.country)))
      .join('text')
      .attr('class', 'country-label')
      .attr('x', (d) => x(d.gini_disp) + (labelOffsets[d.country]?.dx ?? 8))
      .attr('y', (d) => y(d.ige) + (labelOffsets[d.country]?.dy ?? 5))
      .attr('font-size', (d) => d.country === 'United States' ? 12 : 10)
      .attr('font-weight', (d) => d.country === 'United States' ? '700' : '500')
      .attr('fill', (d) => {
        if (d.country === 'United States') return usColor;
        if (nordicLabels.includes(d.country)) return nordicColor;
        return '#444';
      })
      .attr('paint-order', 'stroke')
      .attr('stroke', '#fff')
      .attr('stroke-width', 3)
      .attr('opacity', 0)
      .text((d) => d.country)
      .transition().delay(300).duration(400)
      .attr('opacity', 1);

    // "Nordic benchmarks" caption above the lower-left cluster, anchored to
    // a Nordic country's coords so it tracks projection changes.
    const nordicAnchor = data.find((d) => nordicLabels.includes(d.country));
    if (nordicAnchor) {
      g.append('text')
        .attr('x', x(nordicAnchor.gini_disp) - 18)
        .attr('y', y(nordicAnchor.ige) - 28)
        .attr('text-anchor', 'end')
        .attr('font-size', 11)
        .attr('font-weight', 700)
        .attr('fill', nordicColor)
        .attr('letter-spacing', '0.08em')
        .attr('opacity', 0)
        .text('NORDIC BENCHMARKS')
        .transition().delay(700).duration(400).attr('opacity', 0.9);
    }
  }

  onMount(async () => {
    await loadMergedData();
    drawChart();

    const ro = new ResizeObserver(() => drawChart());
    ro.observe(svgEl);
    return () => ro.disconnect();
  });
</script>

<div class="chart-wrapper">
  <div class="chart-header">
    <div class="title-block">
      <h3>The Great Gatsby Curve</h3>
      <p class="subtitle">More inequality is associated with lower mobility.</p>
    </div>
  </div>

  <div class="svg-wrap">
    <svg bind:this={svgEl} style="width:100%;display:block;"></svg>

    {#if tooltip.visible}
      <div class="tooltip" style="left:{tooltip.x}px;top:{tooltip.y}px">
        <div class="tt-country">{tooltip.country}</div>
        <div class="tt-row">
          <span class="tt-label">Mobility (IGE)</span>
          <span class="tt-val">{tooltip.ige.toFixed(2)}</span>
        </div>
        <div class="tt-row">
          <span class="tt-label">Gini (after tax)</span>
          <span class="tt-val">{tooltip.gini.toFixed(1)}</span>
        </div>
        <div class="tt-row">
          <span class="tt-label">Redistribution gap</span>
          <span class="tt-val" style="color:#2471A3">-{tooltip.absRed.toFixed(1)} pts</span>
        </div>
        <div class="tt-region">{tooltip.region}</div>
      </div>
    {/if}
  </div>

  <div class="chart-footer">
    <div class="region-legend" aria-label="Region colors">
      {#each [...new Set(data.map((d) => d.region))].sort() as region}
        <span class="legend-item"><span class="swatch" style="background:{colorForRegion(region)}"></span>{region}</span>
      {/each}
    </div>
    <div class="citation">
      Sources: World Bank GDIM 2023 (BETA, parent=avg, child=all) · SWIID v9.6 summary (latest year)
    </div>
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
    padding: 20px 20px 14px;
    box-sizing: border-box;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }

  .chart-header {
    margin-bottom: 10px;
  }

  h3 {
    margin: 0 0 4px;
    font-size: 1.15rem;
    font-weight: 800;
    color: #2c3e50;
    letter-spacing: -0.3px;
  }

  .subtitle {
    margin: 0;
    font-size: 0.82rem;
    color: #7f8c8d;
    line-height: 1.4;
  }

  .svg-wrap {
    position: relative;
    flex-grow: 1;
    min-height: 0;
    overflow: hidden;
  }

  .tooltip {
    position: absolute;
    background: rgba(15,15,20,0.93);
    color: #fff;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 12px;
    pointer-events: none;
    white-space: nowrap;
    line-height: 1.6;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    z-index: 10;
  }

  .tt-country {
    font-weight: 700;
    font-size: 13px;
    margin-bottom: 4px;
    color: #fff;
  }

  .tt-row {
    display: flex;
    justify-content: space-between;
    gap: 16px;
  }

  .tt-label { color: #aaa; }
  .tt-val { font-weight: 600; }

  .tt-region {
    margin-top: 4px;
    font-size: 10px;
    color: #888;
    font-style: italic;
  }

  .chart-footer {
    border-top: 1px solid #ecf0f1;
    padding-top: 10px;
    margin-top: 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .region-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    font-size: 0.72rem;
    color: #5f6c75;
  }

  .legend-item {
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }

  .swatch {
    width: 9px;
    height: 9px;
    border-radius: 50%;
  }

  .citation {
    font-size: 0.72rem;
    color: #aaa;
    text-align: right;
  }
</style>

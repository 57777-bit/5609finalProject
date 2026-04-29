<!-- <script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import * as topojson from 'topojson-client';
    
  let svgEl = $state(null);
  let tooltip = $state({ visible: false, x: 0, y: 0, name: '', state: '', value: '' });
  let isLoading = $state(true);

  let data = $state(null);
  let geoData = $state(null);

  onMount(async () => {
  const [rawData, us] = await Promise.all([
      fetch('/data.json').then(r => r.json()),
      fetch('/counties-10m.json').then(r => r.json())
  ]);
  geoData = us;
  data = rawData;       // 最后赋值，触发$effect
  isLoading = false;
  });

  $effect(() => {
  if (data && geoData && svgEl) {
      drawMap(data, geoData);
  }
  });

  function drawMap(data, geoData) {
    const field = 'change_kfr_pooled_pooled_p1';

    const valueMap = new Map(
      data
        .filter(d => d[field] != null)
        .map(d => [d.fips, +d[field]])
    );

    const values = [...valueMap.values()];
    const absMax = d3.quantile(values.map(Math.abs).sort(d3.ascending), 0.95);

    const colorScale = d3.scaleDiverging()
      .domain([-absMax, 0, absMax])
      .interpolator(d3.interpolateRdBu);

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();

    const width = svgEl.clientWidth || 900;
    const height = width * 0.6;
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const counties = topojson.feature(geoData, geoData.objects.counties);
    const projection = d3.geoAlbersUsa().fitSize([width, height], counties);
    const path = d3.geoPath().projection(projection);
    const g = svg.append('g');

    g.selectAll('path')
      .data(counties.features)
      .join('path')
      .attr('d', path)
      .attr('fill', d => {
        const val = valueMap.get(d.id);
        return val != null ? colorScale(val) : '#ccc';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.3)
      .on('mouseover', function(event, d) {
        const val = valueMap.get(d.id);
        const countyInfo = data.find(row => row.fips === d.id);
        d3.select(this).attr('stroke', '#333').attr('stroke-width', 1.5);
        tooltip = {
          visible: true,
          x: event.offsetX + 12,
          y: event.offsetY - 28,
          name: countyInfo?.county_name ?? 'unknown county',
          state: countyInfo?.state_name ?? '',
          value: val != null
            ? (val > 0 ? `+${(val*100).toFixed(1)}` : `${(val*100).toFixed(1)}`)
            : 'no data',
          direction: val > 0 ? 'Improvement' : 'Deterioration'
        };
      })
      .on('mousemove', function(event) {
        tooltip = { ...tooltip, x: event.offsetX + 12, y: event.offsetY - 28 };
      })
      .on('mouseout', function() {
        d3.select(this).attr('stroke', '#fff').attr('stroke-width', 0.3);
        tooltip = { ...tooltip, visible: false };
      });

    g.append('path')
      .datum(topojson.mesh(geoData, geoData.objects.states, (a, b) => a !== b))
      .attr('d', path)
      .attr('fill', 'none')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1);

    // 图例（diverging）
    const legendWidth = 220;
    const legendHeight = 10;
    const legendX = width - legendWidth - 20;
    const legendY = height - 40;

    const defs = svg.append('defs');
    const grad = defs.append('linearGradient').attr('id', 'change-legend-gradient');
    grad.selectAll('stop')
      .data(d3.range(0, 1.01, 0.1))
      .join('stop')
      .attr('offset', d => d)
      .attr('stop-color', d => colorScale(-absMax + d * absMax * 2));

    svg.append('rect')
      .attr('x', legendX).attr('y', legendY)
      .attr('width', legendWidth).attr('height', legendHeight)
      .style('fill', 'url(#change-legend-gradient)');

    svg.append('text')
      .attr('x', legendX).attr('y', legendY + 24)
      .style('font-size', '10px').style('fill', '#555')
      .text('Worsening');

    svg.append('text')
      .attr('x', legendX + legendWidth / 2).attr('y', legendY + 24)
      .attr('text-anchor', 'middle')
      .style('font-size', '10px').style('fill', '#555')
      .text('No change');

    svg.append('text')
      .attr('x', legendX + legendWidth).attr('y', legendY + 24)
      .attr('text-anchor', 'end')
      .style('font-size', '10px').style('fill', '#555')
      .text('Improvement');

    svg.append('text')
      .attr('x', legendX).attr('y', legendY - 6)
      .style('font-size', '11px').style('fill', '#555')
      .text('Change in upward mobility (1978 → 1992 birth cohorts)');
  }
</script>

<div class="map-container">
  <h2>Intergenerational Change: Is Upward Mobility Improving or Worsening?</h2>
  <p class="desc">
    Blue = Children from low-income families born in 1992 have better upward mobility than those born in 1978.
    Red = Conditions are worsening.
  </p>
  {#if isLoading}
    <div class="loading">Loading...</div>
  {:else}
    <div class="wrapper">
      <svg bind:this={svgEl} style="width:100%; display:block;"></svg>
      {#if tooltip.visible}
        <div class="tooltip" style="left:{tooltip.x}px; top:{tooltip.y}px">
          <strong>{tooltip.name}, {tooltip.state}</strong><br/>
          Change in mobility: <strong>{tooltip.value}</strong> percentile points<br/>
          Trend: <strong>{tooltip.direction}</strong>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .map-container { width: 100%; font-family: sans-serif; margin-top: 1rem; }
  h2 { font-size: 1rem; font-weight: 600; margin-bottom: 0.3rem; color: #222; }
  .desc { font-size: 0.85rem; color: #666; margin-bottom: 0.5rem; }
  .wrapper { position: relative; width: 100%; }
  .loading { text-align: center; padding: 4rem; color: #888; }
  .tooltip {
    position: absolute;
    background: rgba(0,0,0,0.8);
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
    pointer-events: none;
    white-space: nowrap;
    line-height: 1.8;
  }
</style> -->

<script>
  import { onMount, onDestroy } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';
  import * as topojson from 'topojson-client';

  let svgEl = $state(null);
  let tooltip = $state({ visible: false, x: 0, y: 0, name: '', state: '', value: '', rank: '' });
  let isLoading = $state(true);
  let activeMode = $state('change');   // 'p1' | 'p100' | 'change'
  let data = $state(null);
  let geoData = $state(null);
  let isPlaying = $state(false);
  let progress = $state(0); // 0 = 1978, 1 = 1992
  let animTimer = null;

  const modes = [
    {
      key: 'p1',
      label: 'Born poor',
      field: 'kfr_pooled_pooled_p1_1978',
      title: 'Upward mobility for children born into poverty',
      desc: 'Adult income rank of children whose parents were at the bottom 1% of income. Greener = better odds of climbing up.',
      diverging: false,
    },
    {
      key: 'p100',
      label: 'Born wealthy',
      field: 'kfr_pooled_pooled_p100_1978',
      title: 'Outcomes for children born into wealthy families',
      desc: 'Adult income rank of children whose parents were at the top 1% of income. Notice how much less variation there is — wealth insulates.',
      diverging: false,
    },
    {
      key: 'change',
      label: 'Change over time',
      field: 'change_kfr_pooled_pooled_p1',
      title: 'Is upward mobility improving or worsening? (1978 → 1992)',
      desc: 'Blue = children born in 1992 have better mobility than those born in 1978. Red = conditions are worsening.',
      diverging: true,
    },
  ];

  onMount(async () => {
    const [rawData, us] = await Promise.all([
      fetch(`${base}/data/data.json`).then(r => r.json()),
      fetch(`${base}/data/counties-10m.json`).then(r => r.json()),
    ]);
    geoData = us;
    data = rawData;
    isLoading = false;
  });

  let updateFill = null;

  $effect(() => {
    if (data && geoData && svgEl) {
      updateFill = drawMap();
    }
  });

  function playAnimation() {
    if (isPlaying) return;
    isPlaying = true;
    progress = 0;
    updateFill?.('reset'); 

    const totalDuration = 2500; 
    const start = performance.now();

    function tick(now) {
      const t = Math.min((now - start) / totalDuration, 1);
      progress = t;
      updateFill?.(t);
      if (t < 1) {
        animTimer = requestAnimationFrame(tick);
      } else {
        isPlaying = false;
      }
    }
    animTimer = requestAnimationFrame(tick);
  }

  function resetAnimation() {
    if (animTimer) cancelAnimationFrame(animTimer);
    isPlaying = false;
    progress = 0;
    d3.select(svgEl).style('opacity', 1);
    updateFill?.(0);
  }

  onDestroy(() => {
    if (animTimer) cancelAnimationFrame(animTimer);
  });

  // function drawMap() {
  //   const mode = modes.find(m => m.key === activeMode);
  //   const field = mode.field;

  //   const valueMap = new Map(
  //     data
  //       .filter(d => d[field] != null)
  //       .map(d => [d.fips, +d[field]])
  //   );

  //   const values = [...valueMap.values()];
  //   let domainLo, domainMid, domainHi;

  //   if (mode.diverging) {
  //     const absMax = d3.quantile(values.map(Math.abs).sort(d3.ascending), 0.95);
  //     domainLo = -absMax; domainMid = 0; domainHi = absMax;
  //   } else {
  //     const sorted = values.slice().sort(d3.ascending);
  //     domainLo = d3.quantile(sorted, 0.05);
  //     domainMid = d3.quantile(sorted, 0.5);
  //     domainHi = d3.quantile(sorted, 0.95);
  //   }

  //   const colorScale = d3.scaleDiverging()
  //     .domain([domainLo, domainMid, domainHi])
  //     .interpolator(d3.interpolateRdBu);

  //   const svg = d3.select(svgEl);
  //   svg.selectAll('*').remove();

  //   const width = svgEl.clientWidth || 900;
  //   const height = width * 0.6;
  //   svg.attr('viewBox', `0 0 ${width} ${height}`);

  //   const counties = topojson.feature(geoData, geoData.objects.counties);
  //   const projection = d3.geoAlbersUsa().fitSize([width, height], counties);
  //   const path = d3.geoPath().projection(projection);
  //   const g = svg.append('g');

  //   g.selectAll('path')
  //     .data(counties.features)
  //     .join('path')
  //     .attr('d', path)
  //     .attr('fill', d => {
  //       const val = valueMap.get(d.id);
  //       return val != null ? colorScale(val) : '#ddd';
  //     })
  //     .attr('stroke', '#fff')
  //     .attr('stroke-width', 0.3)
  //     .on('mouseover', function (event, d) {
  //       const val = valueMap.get(d.id);
  //       const info = data.find(r => r.fips === d.id);
  //       d3.select(this).attr('stroke', '#222').attr('stroke-width', 1.8);

  //       let valueLabel = 'No data';
  //       let rankLabel = '';
  //       if (val != null) {
  //         if (mode.diverging) {
  //           valueLabel = (val > 0 ? '+' : '') + (val * 100).toFixed(1) + ' percentile pts';
  //           rankLabel = val > 0 ? 'Improving' : 'Worsening';
  //         } else {
  //           valueLabel = 'Income rank: ' + (val * 100).toFixed(1) + 'th percentile';
  //           rankLabel = val > 0.5 ? 'Above national median' : 'Below national median';
  //         }
  //       }

  //       tooltip = {
  //         visible: true,
  //         x: event.offsetX + 14,
  //         y: event.offsetY - 36,
  //         name: info?.county_name ?? 'Unknown county',
  //         state: info?.state_name ?? '',
  //         value: valueLabel,
  //         rank: rankLabel,
  //       };
  //     })
  //     .on('mousemove', function (event) {
  //       tooltip = { ...tooltip, x: event.offsetX + 14, y: event.offsetY - 36 };
  //     })
  //     .on('mouseout', function () {
  //       d3.select(this).attr('stroke', '#fff').attr('stroke-width', 0.3);
  //       tooltip = { ...tooltip, visible: false };
  //     });

  //   // State borders
  //   g.append('path')
  //     .datum(topojson.mesh(geoData, geoData.objects.states, (a, b) => a !== b))
  //     .attr('d', path)
  //     .attr('fill', 'none')
  //     .attr('stroke', '#fff')
  //     .attr('stroke-width', 1);

  //   // Legend
  //   const legendWidth = 240;
  //   const legendHeight = 10;
  //   const legendX = width - legendWidth - 20;
  //   const legendY = height - 44;

  //   const defs = svg.append('defs');
  //   const grad = defs.append('linearGradient').attr('id', 'legend-grad');

  //   const stops = d3.range(0, 1.01, 0.05);
  //   grad.selectAll('stop')
  //     .data(stops)
  //     .join('stop')
  //     .attr('offset', d => d)
  //     .attr('stop-color', d => colorScale(domainLo + d * (domainHi - domainLo)));

  //   svg.append('rect')
  //     .attr('x', legendX).attr('y', legendY)
  //     .attr('width', legendWidth).attr('height', legendHeight)
  //     .style('fill', 'url(#legend-grad)')
  //     .attr('rx', 3);

  //   const legendLabels = mode.diverging
  //     ? ['Worsening', 'No change', 'Improving']
  //     : ['Low mobility', 'Median', 'High mobility'];

  //   legendLabels.forEach((label, i) => {
  //     svg.append('text')
  //       .attr('x', legendX + (i * legendWidth / 2))
  //       .attr('y', legendY + 24)
  //       .attr('text-anchor', i === 0 ? 'start' : i === 1 ? 'middle' : 'end')
  //       .style('font-size', '10px')
  //       .style('fill', '#555')
  //       .text(label);
  //   });

  //   svg.append('text')
  //     .attr('x', legendX)
  //     .attr('y', legendY - 7)
  //     .style('font-size', '11px')
  //     .style('fill', '#444')
  //     .style('font-weight', '500')
  //     .text(mode.diverging ? 'Change in mobility (1978 → 1992)' : 'Adult income rank (percentile)');
  // }

  function drawMap() {
    if (!svgEl || !data || !geoData) return;

    const field78 = 'kfr_pooled_pooled_p1_1978';
    const field92 = 'kfr_pooled_pooled_p1_1992';

    const valueMap78 = new Map(
      data.filter(d => d[field78] != null)
        .map(d => [d.fips, +d[field78]])
    );
    const valueMap92 = new Map(
      data.filter(d => d[field92] != null)
        .map(d => [d.fips, +d[field92]])
    );

    const allValues = [
      ...valueMap78.values(),
      ...valueMap92.values()
    ];
    const lo = d3.quantile(allValues.slice().sort(d3.ascending), 0.05);
    const hi = d3.quantile(allValues.slice().sort(d3.ascending), 0.95);

    const colorScale = d3.scaleSequential()
      .domain([lo, hi])
      .interpolator(d3.interpolateRdBu);

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();

    const W = svgEl.clientWidth || 900;
    const H = Math.round(W * 0.62);
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const counties = topojson.feature(geoData, geoData.objects.counties);
    // Reserve a top strip so the legend at the top does not cover any county.
    const TOP_PAD = 56;
    const proj = d3.geoAlbersUsa().fitExtent(
      [[0, TOP_PAD], [W, H]],
      counties
    );
    const path = d3.geoPath(proj);

    const g = svg.append('g');

    g.selectAll('path.county')
      .data(counties.features)
      .join('path')
      .attr('class', 'county')
      .attr('d', path)
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.3)
      .attr('fill', d => {
        const v78 = valueMap78.get(d.id) ?? valueMap78.get(String(d.id).padStart(5,'0'));
        return v78 != null ? colorScale(v78) : '#ddd';
      })
      .on('mouseover', function(ev, d) {
        const fips = String(d.id).padStart(5, '0');
        const v78 = valueMap78.get(d.id) ?? valueMap78.get(fips);
        const v92 = valueMap92.get(d.id) ?? valueMap92.get(fips);
        const info = data.find(r => r.fips === d.id || String(r.fips).padStart(5,'0') === fips);
        d3.select(this).attr('stroke', '#333').attr('stroke-width', 1.5);
        const rect = svgEl.getBoundingClientRect();
        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top - 10,
          name: info?.county_name ?? 'Unknown',
          state: info?.state_name ?? '',
          v78: v78 != null ? (v78 * 100).toFixed(1) : null,
          v92: v92 != null ? (v92 * 100).toFixed(1) : null,
          change: (v78 != null && v92 != null)
            ? ((v92 - v78) * 100).toFixed(1)
            : null,
        };
      })
      .on('mousemove', function(ev) {
        const rect = svgEl.getBoundingClientRect();
        tooltip = { ...tooltip, x: ev.clientX - rect.left + 12, y: ev.clientY - rect.top - 10 };
      })
      .on('mouseleave', function() {
        d3.select(this).attr('stroke', '#fff').attr('stroke-width', 0.3);
        tooltip = { ...tooltip, visible: false };
      });

    svg.append('path')
      .datum(topojson.mesh(geoData, geoData.objects.states, (a, b) => a !== b))
      .attr('d', path)
      .attr('fill', 'none')
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.9);

    // Region labels anchor the prose mentions of "South" and "Midwest" to the map.
    // Each label is centered on a representative state so the narrative has a visual target.
    const states = topojson.feature(geoData, geoData.objects.states);
    const REGION_ANCHORS = [
      { label: 'SOUTH',   stateId: '47' }, // Tennessee — central to the Census South
      { label: 'MIDWEST', stateId: '19' }, // Iowa — central to the Census Midwest
    ];
    REGION_ANCHORS.forEach(({ label, stateId }) => {
      const f = states.features.find(s => String(s.id) === stateId);
      if (!f) return;
      const [cx, cy] = path.centroid(f);
      if (!Number.isFinite(cx)) return;
      svg.append('text')
        .attr('x', cx).attr('y', cy)
        .attr('text-anchor', 'middle')
        .attr('font-size', 18)
        .attr('font-weight', 700)
        .attr('fill', '#5a3033')
        .attr('opacity', 0.55)
        .attr('paint-order', 'stroke')
        .attr('stroke', '#fff')
        .attr('stroke-width', 3)
        .style('letter-spacing', '0.18em')
        .style('pointer-events', 'none')
        .text(label);
    });

    // Legend pinned to the top-right strip reserved by TOP_PAD; no county is covered.
    const lgW = 200, lgH = 10;
    const lgX = W - lgW - 20;
    const lgY = 16;
    const defs = svg.append('defs');
    const grad = defs.append('linearGradient').attr('id', 'cm-grad');
    d3.range(0, 1.01, 0.1).forEach(t => {
      grad.append('stop').attr('offset', t)
        .attr('stop-color', colorScale(lo + t * (hi - lo)));
    });
    svg.append('rect').attr('x', lgX).attr('y', lgY)
      .attr('width', lgW).attr('height', lgH).attr('rx', 3)
      .attr('fill', 'url(#cm-grad)');
    [['Low mobility', 'start', lgX], ['High mobility', 'end', lgX + lgW]].forEach(([label, anchor, x]) => {
      svg.append('text').attr('x', x).attr('y', lgY + 24)
        .attr('text-anchor', anchor).style('font-size', '10px').style('fill', '#555').text(label);
    });

    const countyOrder = counties.features
      .map(d => {
        const fips = String(d.id).padStart(5, '0');
        const v78 = valueMap78.get(d.id) ?? valueMap78.get(fips);
        const v92 = valueMap92.get(d.id) ?? valueMap92.get(fips);
        const absChange = (v78 != null && v92 != null)
          ? Math.abs(v92 - v78)
          : 0;
        return { id: d.id, fips, absChange };
      })
      .sort((a, b) => b.absChange - a.absChange); 
    const triggerMap = new Map();
    countyOrder.forEach((d, i) => {
      const triggerT = (i / countyOrder.length) * 0.8;
      triggerMap.set(d.id, triggerT);
      triggerMap.set(d.fips, triggerT);
    });

    return function updateFill(t) {
      g.selectAll('path.county')
        .attr('fill', d => {
          const fips = String(d.id).padStart(5, '0');
          const v78 = valueMap78.get(d.id) ?? valueMap78.get(fips);
          const v92 = valueMap92.get(d.id) ?? valueMap92.get(fips);
          if (v78 == null && v92 == null) return '#ddd';

          const triggerT = triggerMap.get(d.id) ?? triggerMap.get(fips) ?? 0;

          // 每个县有0.15的过渡窗口
          const localT = Math.max(0, Math.min(1, (t - triggerT) / 0.15));
          const v = v78 != null && v92 != null
            ? v78 + (v92 - v78) * localT
            : (v78 ?? v92);
          return colorScale(v);
        });
    };
  }


</script>

<!-- <div class="map-container">
  {#if isLoading}
    <div class="loading">Loading map data...</div>
  {:else}
    <div class="wrapper">
      <svg bind:this={svgEl} style="width:100%; display:block;"></svg>
      {#if tooltip.visible}
        <div class="tooltip" style="left:{tooltip.x}px; top:{tooltip.y}px">
          <strong>{tooltip.name}, {tooltip.state}</strong><br />
          {tooltip.value}<br />
          <span class="trend">{tooltip.rank}</span>
        </div>
      {/if}
    </div>
  {/if}
</div> -->
<div class="map-wrap">
  {#if isLoading}
    <p class="map-loading">Loading…</p>
  {:else}
  <div class="control-bar">
    <div class="year-display">
      <span class="year-tag" class:active={progress < 0.5}>1978</span>
      <span class="year-arrow">→</span>
      <span class="year-tag" class:active={progress >= 0.5}>1992</span>
    </div>
    <div class="status-text">
      {#if isPlaying && progress < 0.5}
        Showing 1978 baseline…
      {:else if isPlaying}
        Transitioning to 1992…
      {:else if progress >= 1}
        1992 — compare the changes
      {:else}
        1978 — where mobility stood
      {/if}
    </div>
    <button class="play-btn" onclick={playAnimation} disabled={isPlaying}>
      {progress > 0 && !isPlaying ? '↺ Replay' : '▶ Play'}
    </button>
    {#if progress > 0 && !isPlaying}
      <button class="reset-btn" onclick={resetAnimation}>Reset</button>
    {/if}
  </div>

    <svg bind:this={svgEl} style="width:100%;display:block;"></svg>

    <!-- tooltip -->
    {#if tooltip.visible}
      <div class="tooltip" style="left:{tooltip.x}px;top:{tooltip.y}px">
        <strong>{tooltip.name}, {tooltip.state}</strong><br/>
        1978 mobility: <strong>{tooltip.v78 ?? 'no data'}th</strong><br/>
        1992 mobility: <strong>{tooltip.v92 ?? 'no data'}th</strong><br/>
        {#if tooltip.change != null}
          Change: <strong style="color:{+tooltip.change > 0 ? '#2471A3' : '#C0392B'}">
            {+tooltip.change > 0 ? '+' : ''}{tooltip.change} pts
          </strong>
        {/if}
      </div>
    {/if}
  {/if}
</div>

<style>
  .map-container {
    width: 100%;
    font-family: sans-serif;
    margin-top: 1rem;
  }

  .toggle-bar {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .toggle-btn {
    padding: 0.4rem 1rem;
    border: 1.5px solid #ccc;
    border-radius: 20px;
    background: white;
    cursor: pointer;
    font-size: 0.85rem;
    color: #444;
    transition: all 0.3s ease;
    animation: btnPulse 2s ease-in-out infinite;
  }

  .toggle-btn:nth-child(1) { animation-delay: 0s; }
  .toggle-btn:nth-child(2) { animation-delay: 0.3s; }
  .toggle-btn:nth-child(3) { animation-delay: 0.6s; }

  .toggle-btn:hover {
    border-color: #2c5f8a;
    color: #111;
    transform: translateY(-2px);
    box-shadow: 0 3px 8px rgba(44, 95, 138, 0.2);
  }

  .toggle-btn.active {
    background: #2c5f8a;
    border-color: #2c5f8a;
    color: white;
    font-weight: 600;
    animation: none;
    box-shadow: 0 2px 8px rgba(44, 95, 138, 0.3);
  }

  @keyframes btnPulse {
    0%, 100% { border-color: #ccc; box-shadow: 0 0 0 0 rgba(44, 95, 138, 0); transform: scale(1); }
    50% { border-color: #2c5f8a; box-shadow: 0 0 0 4px rgba(44, 95, 138, 0.12); transform: scale(1.03); }
  }

  /* h2 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.3rem;
    color: #222;
  }

  .desc {
    font-size: 0.85rem;
    color: #666;
    margin-bottom: 0.6rem;
  }

  .insight {
    background: #f5f8fc;
    border-left: 3px solid #2c5f8a;
    padding: 0.6rem 0.9rem;
    border-radius: 0 6px 6px 0;
    font-size: 0.85rem;
    color: #333;
    margin-bottom: 0.8rem;
    line-height: 1.5;
  }

  .wrapper {
    position: relative;
    width: 100%;
  }

  .loading {
    text-align: center;
    padding: 4rem;
    color: #888;
  }

  .tooltip {
    position: absolute;
    background: rgba(20, 20, 20, 0.88);
    color: white;
    padding: 8px 13px;
    border-radius: 7px;
    font-size: 13px;
    pointer-events: none;
    white-space: nowrap;
    line-height: 1.9;
  }

  .trend {
    font-size: 11px;
    opacity: 0.75;
    font-style: italic;
  }

  .compare-hint {
    font-size: 0.8rem;
    color: #888;
    margin-top: 0.5rem;
    text-align: center;
    font-style: italic;
  } */

  .map-wrap {
    position: relative;
    width: 100%;
  }

  .map-loading {
    text-align: center;
    padding: 4rem;
    color: #888;
  }

  .tooltip {
    position: absolute;
    background: rgba(15, 15, 15, 0.9);
    color: #fff;
    padding: 8px 13px;
    border-radius: 7px;
    font-size: 13px;
    pointer-events: none;
    white-space: nowrap;
    line-height: 1.7;
    box-shadow: 0 4px 16px rgba(0,0,0,.25);
    z-index: 10;
  }

  .control-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    background: #f8f9fa;
    border-bottom: 1px solid #e0e0e0;
  }
  .year-display {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .year-tag {
    font-size: 15px;
    font-weight: 700;
    color: #bbb;
    transition: color 0.4s, transform 0.4s;
  }
  .year-tag.active {
    color: #2c3e50;
    transform: scale(1.1);
  }
  .year-arrow {
    font-size: 13px;
    color: #ccc;
  }
  .status-text {
    flex: 1;
    font-size: 12px;
    color: #888;
    font-style: italic;
  }
</style>
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
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';
  import * as topojson from 'topojson-client';

  let svgEl = $state(null);
  let tooltip = $state({ visible: false, x: 0, y: 0, name: '', state: '', value: '', rank: '' });
  let isLoading = $state(true);
  let activeMode = $state('change');   // 'p1' | 'p100' | 'change'
  let data = $state(null);
  let geoData = $state(null);

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

  $effect(() => {
    if (data && geoData && svgEl) drawMap();
  });

  $effect(() => {
    activeMode;
    if (data && geoData && svgEl) drawMap();
  });

  function drawMap() {
    const mode = modes.find(m => m.key === activeMode);
    const field = mode.field;

    const valueMap = new Map(
      data
        .filter(d => d[field] != null)
        .map(d => [d.fips, +d[field]])
    );

    const values = [...valueMap.values()];
    let domainLo, domainMid, domainHi;

    if (mode.diverging) {
      const absMax = d3.quantile(values.map(Math.abs).sort(d3.ascending), 0.95);
      domainLo = -absMax; domainMid = 0; domainHi = absMax;
    } else {
      const sorted = values.slice().sort(d3.ascending);
      domainLo = d3.quantile(sorted, 0.05);
      domainMid = d3.quantile(sorted, 0.5);
      domainHi = d3.quantile(sorted, 0.95);
    }

    const colorScale = d3.scaleDiverging()
      .domain([domainLo, domainMid, domainHi])
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
        return val != null ? colorScale(val) : '#ddd';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.3)
      .on('mouseover', function (event, d) {
        const val = valueMap.get(d.id);
        const info = data.find(r => r.fips === d.id);
        d3.select(this).attr('stroke', '#222').attr('stroke-width', 1.8);

        let valueLabel = 'No data';
        let rankLabel = '';
        if (val != null) {
          if (mode.diverging) {
            valueLabel = (val > 0 ? '+' : '') + (val * 100).toFixed(1) + ' percentile pts';
            rankLabel = val > 0 ? 'Improving' : 'Worsening';
          } else {
            valueLabel = 'Income rank: ' + (val * 100).toFixed(1) + 'th percentile';
            rankLabel = val > 0.5 ? 'Above national median' : 'Below national median';
          }
        }

        tooltip = {
          visible: true,
          x: event.offsetX + 14,
          y: event.offsetY - 36,
          name: info?.county_name ?? 'Unknown county',
          state: info?.state_name ?? '',
          value: valueLabel,
          rank: rankLabel,
        };
      })
      .on('mousemove', function (event) {
        tooltip = { ...tooltip, x: event.offsetX + 14, y: event.offsetY - 36 };
      })
      .on('mouseout', function () {
        d3.select(this).attr('stroke', '#fff').attr('stroke-width', 0.3);
        tooltip = { ...tooltip, visible: false };
      });

    // State borders
    g.append('path')
      .datum(topojson.mesh(geoData, geoData.objects.states, (a, b) => a !== b))
      .attr('d', path)
      .attr('fill', 'none')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1);

    // Legend
    const legendWidth = 240;
    const legendHeight = 10;
    const legendX = width - legendWidth - 20;
    const legendY = height - 44;

    const defs = svg.append('defs');
    const grad = defs.append('linearGradient').attr('id', 'legend-grad');

    const stops = d3.range(0, 1.01, 0.05);
    grad.selectAll('stop')
      .data(stops)
      .join('stop')
      .attr('offset', d => d)
      .attr('stop-color', d => colorScale(domainLo + d * (domainHi - domainLo)));

    svg.append('rect')
      .attr('x', legendX).attr('y', legendY)
      .attr('width', legendWidth).attr('height', legendHeight)
      .style('fill', 'url(#legend-grad)')
      .attr('rx', 3);

    const legendLabels = mode.diverging
      ? ['Worsening', 'No change', 'Improving']
      : ['Low mobility', 'Median', 'High mobility'];

    legendLabels.forEach((label, i) => {
      svg.append('text')
        .attr('x', legendX + (i * legendWidth / 2))
        .attr('y', legendY + 24)
        .attr('text-anchor', i === 0 ? 'start' : i === 1 ? 'middle' : 'end')
        .style('font-size', '10px')
        .style('fill', '#555')
        .text(label);
    });

    svg.append('text')
      .attr('x', legendX)
      .attr('y', legendY - 7)
      .style('font-size', '11px')
      .style('fill', '#444')
      .style('font-weight', '500')
      .text(mode.diverging ? 'Change in mobility (1978 → 1992)' : 'Adult income rank (percentile)');
  }


</script>

<div class="map-container">

  <!-- Toggle buttons -->
  <div class="toggle-bar">
    {#each modes as mode}
      <button
        class="toggle-btn"
        class:active={activeMode === mode.key}
        onclick={() => activeMode = mode.key}
      >
        {mode.label}
      </button>
    {/each}
  </div>

  <!-- Title + description (reactive) -->
  {#each modes as mode}
    {#if activeMode === mode.key}
      <h2>{mode.title}</h2>
      <p class="desc">{mode.desc}</p>
    {/if}
  {/each}

  <!-- Insight callout (changes per mode) -->
  <div class="insight">
    {#if activeMode === 'p1'}
      <strong>Key finding:</strong> Geography dramatically shapes the fate of children born poor.
      Counties in the Mountain West and upper Midwest show much stronger upward mobility than
      parts of the Deep South or Appalachia — for the exact same starting income level.
    {:else if activeMode === 'p100'}
      <strong>Key finding:</strong> Wealthy families are largely insulated from geography.
      The map is far more uniform — children born rich tend to stay near the top regardless of county.
      This contrast with the "born poor" map reveals that geography is a trap mainly for the disadvantaged.
    {:else}
      <strong>Key finding:</strong> Mobility is declining in many counties, especially in the South and Midwest.
      Children born in 1992 in these areas face worse odds than those born in 1978 — the American Dream
      is fading fastest in the places that needed it most.
    {/if}
  </div>

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

  <!-- Comparison note (only shown when viewing p1 or p100) -->
  {#if activeMode !== 'change'}
    <p class="compare-hint">
      Switch between "Born poor" and "Born wealthy" to see how geography affects children differently depending on their starting point.
    </p>
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
    transition: all 0.2s;
  }

  .toggle-btn:hover {
    border-color: #888;
    color: #111;
  }

  .toggle-btn.active {
    background: #2c5f8a;
    border-color: #2c5f8a;
    color: white;
    font-weight: 600;
  }

  h2 {
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
  }
</style>
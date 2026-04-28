<!-- <!-- <script module>
  export const THRESHOLD_LO = 40;
  export const THRESHOLD_HI = 50;

  export const STEPS = [
    {
      id: 0,
      title: "The Geographic Lottery",
      content: "For children born into low-income families, their adult economic success is highly dependent on their specific county of birth. Why does a zip code matter so much in the U.S.?"
    },
    {
      id: 1,
      title: "Most stay stuck.",
      content: "In the majority of U.S. counties, children born into the poorest families reach only the 25th–40th income percentile as adults. They end up poorer than most of their peers — just as their parents were.",
      statNum: "~60%",
      statLabel: "of counties leave poor kids below the 40th percentile",
      statColor: "#C0392B"
    },
    {
      id: 2,
      title: "Some tread water.",
      content: "A smaller share of counties land near the middle — children reaching roughly the 40th–50th percentile. They escape the very bottom, but haven't truly climbed.",
      statNum: "~20%",
      statLabel: "of counties produce outcomes near the national median",
      statColor: "#D4A017"
    },
    {
      id: 3,
      title: "Very few actually climb.",
      content: "Only in a minority of counties — concentrated in the Upper Midwest — do poor kids consistently exceed the 50th percentile. These places are the exception, not the rule.",
      statNum: "~20%",
      statLabel: "of counties enable real upward mobility",
      statColor: "#2471A3"
    },
  ];
</script>


<script>

  import { onMount, onDestroy } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';
  import * as topojson from 'topojson-client';

  // ── Bindable: parent reads/writes the current map step ──
  let { mapStep = $bindable(0) } = $props();

  let svgEl      = $state(null);
  let mapLoading = $state(true);
  let tooltip    = $state({ visible: false, x: 0, y: 0, name: '', state: '', p1: null });

  let countyMap = new Map();
  let geoData   = null;
  let observers = [];

  // ── Preprocess raw Opportunity Atlas → {fips: {name, state, p1}} ──
  function preprocess(raw) {
    const m = new Map();
    for (const row of raw) {
      if (!row.fips) continue;
      const v = row['kfr_pooled_pooled_p1_1978'];
      if (v == null) continue;
      m.set(row.fips, {
        name:  row.county_name ?? 'Unknown County',
        state: row.state_name  ?? '',
        p1:    +v * 100,
      });
    }
    return m;
  }

  // ── County fill color ──
  function countyFill(p1, step) {
    if (p1 == null) return '#e8e8e8';
    if (p1 < THRESHOLD_LO)       return step >= 1 ? '#C0392B' : '#e8e8e8';
    else if (p1 <= THRESHOLD_HI) return step >= 2 ? '#D4A017' : '#e8e8e8';
    else                          return step >= 3 ? '#2471A3' : '#e8e8e8';
  }

  // ── Draw (first time) or recolor (subsequent steps) ──
  function drawMap(step) {
    if (!svgEl || !geoData || countyMap.size === 0) return;

    const existing = d3.select(svgEl).select('g.counties');
    if (!existing.empty()) {
      existing.selectAll('path.county')
        .transition().duration(1200).ease(d3.easeCubicInOut)
        .attr('fill', d => countyFill(countyMap.get(d.id)?.p1 ?? null, step));
      return;
    }

    const W = svgEl.clientWidth || 600;
    const H = Math.round(W * 0.62);
    const svg = d3.select(svgEl);
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const counties = topojson.feature(geoData, geoData.objects.counties);
    const proj = d3.geoAlbersUsa().fitSize([W, H], counties);
    const path = d3.geoPath(proj);
    const g = svg.append('g').attr('class', 'counties');

    g.selectAll('path.county')
      .data(counties.features)
      .join('path')
      .attr('class', 'county')
      .attr('d', path)
      .attr('fill', d => countyFill(countyMap.get(d.id)?.p1 ?? null, step))
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.25)
      .on('mouseenter', function(ev, d) {
        d3.select(this).raise().attr('stroke', '#333').attr('stroke-width', 1.5);
        const c = countyMap.get(d.id);
        const rect = svgEl.getBoundingClientRect();
        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top  - 10,
          name:  c?.name  ?? 'Unknown',
          state: c?.state ?? '',
          p1:    c?.p1    ?? null,
        };
      })
      .on('mousemove', function(ev) {
        const rect = svgEl.getBoundingClientRect();
        tooltip = { ...tooltip,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top  - 10 };
      })
      .on('mouseleave', function() {
        d3.select(this).attr('stroke', '#fff').attr('stroke-width', 0.25);
        tooltip = { ...tooltip, visible: false };
      });

    svg.append('path')
      .datum(topojson.mesh(geoData, geoData.objects.states, (a, b) => a !== b))
      .attr('d', path).attr('fill', 'none').attr('stroke', '#fff').attr('stroke-width', 0.9);

    // Legend
    const lg = [
      { c: '#C0392B', l: 'Stuck (< 40th pctile)'   },
      { c: '#999',    l: 'Treading water (40–50th)' },
      { c: '#2471A3', l: 'Climbing (> 50th pctile)' },
    ];
    const lG = svg.append('g').attr('transform', `translate(10,${H - 54})`);
    lg.forEach((item, i) => {
      lG.append('rect').attr('x',0).attr('y',i*17).attr('width',11).attr('height',11).attr('rx',2).attr('fill',item.c);
      lG.append('text').attr('x',16).attr('y',i*17+9.5).attr('font-size',10).attr('fill','#444').text(item.l);
    });
  }

  // Redraw when mapStep changes
  $effect(() => { if (!mapLoading) drawMap(mapStep); });

  onMount(async () => {
    const [rawData, us] = await Promise.all([
      fetch(`${base}/data/data.json`).then(r => r.json()),
      fetch(`${base}/data/counties-10m.json`).then(r => r.json()),
    ]);
    countyMap  = preprocess(rawData);
    geoData    = us;
    mapLoading = false;
  });

  onDestroy(() => observers.forEach(o => o.disconnect()));
</script>

 ── Map SVG (place this in the right sticky column) ── 
<div class="map-wrap">
  {#if mapLoading}
    <p class="map-loading">Loading map…</p>
  {:else}
    <svg bind:this={svgEl} style="width:100%;display:block;"></svg>

    {#if tooltip.visible}
      <div class="tooltip" style="left:{tooltip.x}px;top:{tooltip.y}px">
        <strong>{tooltip.name}, {tooltip.state}</strong><br/>
        Poor kids' adult rank:
        <strong style="color:{
          tooltip.p1 == null      ? '#aaa'     :
          tooltip.p1 < THRESHOLD_LO  ? '#C0392B' :
          tooltip.p1 <= THRESHOLD_HI ? '#777'    : '#2471A3'
        }">
          {tooltip.p1 != null ? tooltip.p1.toFixed(1) + 'th percentile' : 'no data'}
        </strong>
      </div>
    {/if}

    <!-- Progress dots 
    <div class="step-dots">
      {#each [{s:1,c:'#C0392B'},{s:2,c:'#999'},{s:3,c:'#2471A3'}] as d}
        <div class="dot" class:active={mapStep >= d.s} style="--c:{d.c}"></div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .map-wrap {
    position: relative;
    width: 100%;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 16px rgba(0,0,0,.08);
  }
  .map-loading { color: #aaa; font-size: 1rem; padding: 2rem; text-align: center; }

  .step-dots {
    display: flex;
    justify-content: center;
    gap: 10px;
    padding: 8px 0;
    background: #fff;
  }
  .dot {
    width: 9px; height: 9px;
    border-radius: 50%;
    background: #ddd;
    transition: background .4s, transform .3s;
  }
  .dot.active { background: var(--c); transform: scale(1.3); }

  .tooltip {
    position: absolute;
    background: rgba(15,15,15,.9);
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

  .chart-box :global(.map-wrap) {
    width: 100%;
    height: 100%;
  }
</style> -->


<!-- <script module>
  export const THRESHOLD_LO = 40;
  export const THRESHOLD_HI = 50;

  export const STEPS = [
    {
      id: 0,
      title: "The Geographic Lottery",
      content: "For children born into low-income families, their adult economic success is highly dependent on their specific county of birth. Why does a zip code matter so much in the U.S.?",
    },
    {
      id: 1,
      title: "Most stay stuck.",
      content: "In the majority of U.S. counties, children born into the poorest families reach only the 25th–40th income percentile as adults. They end up poorer than most of their peers — just as their parents were.",
      statNum: "~60%",
      statLabel: "of counties leave poor kids below the 40th percentile",
      statColor: "#C0392B"
    },
    {
      id: 2,
      title: "Some tread water.",
      content: "A smaller share of counties land near the middle — children reaching roughly the 40th–50th percentile. They escape the very bottom, but haven't truly climbed.",
      statNum: "~20%",
      statLabel: "of counties produce outcomes near the national median",
      statColor: "#D4A017"
    },
    {
      id: 3,
      title: "Very few actually climb.",
      content: "Only in a minority of counties — concentrated in the Upper Midwest — do poor kids consistently exceed the 50th percentile. These places are the exception, not the rule.",
      statNum: "~20%",
      statLabel: "of counties enable real upward mobility",
      statColor: "#2471A3"
    },
  ];
</script>

<script>
  import { onMount, onDestroy } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';
  import * as topojson from 'topojson-client';

  let { mapStep = $bindable(0) } = $props();

  let svgEl      = $state(null);
  let bubbleSvgEl = $state(null);
  let mapLoading = $state(true);
  let tooltip    = $state({ visible: false, x: 0, y: 0, name: '', state: '', p1: null });
  let viewMode   = $state('map'); // 'map' | 'bubble'

  let countyMap = new Map();
  let stateMap  = new Map(); // fips prefix → aggregated state data
  let geoData   = null;

  // ── Preprocess raw data ──
  function preprocess(raw) {
    const m = new Map();
    const stateAgg = new Map(); // stateName → { totalKids, weightedP1 }

    for (const row of raw) {
      if (!row.fips) continue;
      const v = row['kfr_pooled_pooled_p1_1978'];
      if (v == null) continue;
      const p1 = +v * 100;
      const kids = +(row['count_pooled_pooled_p1_1978'] ?? row['n'] ?? 1000);
      m.set(row.fips, {
        name:  row.county_name ?? 'Unknown County',
        state: row.state_name  ?? '',
        p1,
        kids,
      });
      // Aggregate by state
      const st = row.state_name ?? 'Unknown';
      if (!stateAgg.has(st)) stateAgg.set(st, { totalKids: 0, weightedP1: 0 });
      const s = stateAgg.get(st);
      s.totalKids   += kids;
      s.weightedP1  += p1 * kids;
    }

    // Finalize state averages
    for (const [st, agg] of stateAgg) {
      stateMap.set(st, {
        name: st,
        totalKids: agg.totalKids,
        avgP1: agg.totalKids > 0 ? agg.weightedP1 / agg.totalKids : null,
      });
    }
    return m;
  }

  // ── County fill color ──
  function countyFill(p1, step) {
    if (p1 == null) return '#e8e8e8';
    if (p1 < THRESHOLD_LO)       return step >= 1 ? '#C0392B' : '#e8e8e8';
    else if (p1 <= THRESHOLD_HI) return step >= 2 ? '#D4A017' : '#e8e8e8';
    else                          return step >= 3 ? '#2471A3' : '#e8e8e8';
  }

  function bubbleColor(avgP1) {
    if (avgP1 == null) return '#aaa';
    if (avgP1 < THRESHOLD_LO)       return '#C0392B';
    else if (avgP1 <= THRESHOLD_HI) return '#D4A017';
    else                             return '#2471A3';
  }

  // ── Draw choropleth map ──
  function drawMap(step) {
    if (!svgEl || !geoData || countyMap.size === 0) return;

    const existing = d3.select(svgEl).select('g.counties');
    if (!existing.empty()) {
      existing.selectAll('path.county')
        .transition().duration(1200).ease(d3.easeCubicInOut)
        .attr('fill', d => countyFill(countyMap.get(d.id)?.p1 ?? null, step));
      return;
    }

    const W = svgEl.clientWidth || 600;
    const H = Math.round(W * 0.62);
    const svg = d3.select(svgEl);
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const counties = topojson.feature(geoData, geoData.objects.counties);
    const proj = d3.geoAlbersUsa().fitSize([W, H], counties);
    const path = d3.geoPath(proj);
    const g = svg.append('g').attr('class', 'counties');

    g.selectAll('path.county')
      .data(counties.features)
      .join('path')
      .attr('class', 'county')
      .attr('d', path)
      .attr('fill', d => countyFill(countyMap.get(d.id)?.p1 ?? null, step))
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.25)
      .on('mouseenter', function(ev, d) {
        d3.select(this).raise().attr('stroke', '#333').attr('stroke-width', 1.5);
        const c = countyMap.get(d.id);
        const rect = svgEl.getBoundingClientRect();
        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top  - 10,
          name:  c?.name  ?? 'Unknown',
          state: c?.state ?? '',
          p1:    c?.p1    ?? null,
        };
      })
      .on('mousemove', function(ev) {
        const rect = svgEl.getBoundingClientRect();
        tooltip = { ...tooltip,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top  - 10 };
      })
      .on('mouseleave', function() {
        d3.select(this).attr('stroke', '#fff').attr('stroke-width', 0.25);
        tooltip = { ...tooltip, visible: false };
      });

    svg.append('path')
      .datum(topojson.mesh(geoData, geoData.objects.states, (a, b) => a !== b))
      .attr('d', path).attr('fill', 'none').attr('stroke', '#fff').attr('stroke-width', 0.9);

    const lg = [
      { c: '#C0392B', l: 'Stuck (< 40th pctile)'   },
      { c: '#D4A017',    l: 'Treading water (40–50th)' },
      { c: '#2471A3', l: 'Climbing (> 50th pctile)' },
    ];
    const lG = svg.append('g').attr('transform', `translate(10,${H - 54})`);
    lg.forEach((item, i) => {
      lG.append('rect').attr('x',0).attr('y',i*17).attr('width',11).attr('height',11).attr('rx',2).attr('fill',item.c);
      lG.append('text').attr('x',16).attr('y',i*17+9.5).attr('font-size',10).attr('fill','#444').text(item.l);
    });
  }

  // ── Draw bubble map ──
  function drawBubbleMap() {
    if (!bubbleSvgEl || !geoData || stateMap.size === 0) return;

    const W = bubbleSvgEl.clientWidth || 600;
    const H = Math.round(W * 0.62);
    const svg = d3.select(bubbleSvgEl);
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    // Use state centroids from topojson
    const states = topojson.feature(geoData, geoData.objects.states);
    const counties = topojson.feature(geoData, geoData.objects.counties);
    const proj = d3.geoAlbersUsa().fitSize([W, H], counties);
    const path = d3.geoPath(proj);

    // Draw gray state base map
    svg.append('g')
      .selectAll('path')
      .data(states.features)
      .join('path')
      .attr('d', path)
      .attr('fill', '#f0f0f0')
      .attr('stroke', '#ccc')
      .attr('stroke-width', 0.5);

    // Build state name → centroid + data
    const stateDataPoints = [];
    for (const feat of states.features) {
      const centroid = path.centroid(feat);
      if (!centroid || isNaN(centroid[0])) continue;

      // Match state name from countyMap
      // geoData states have numeric FIPS; find a county in that state
      const stateFips = feat.id;
      let stateName = null;
      for (const [fips, county] of countyMap) {
        if (String(fips).padStart(5,'0').startsWith(String(stateFips).padStart(2,'0'))) {
          stateName = county.state;
          break;
        }
      }
      if (!stateName || !stateMap.has(stateName)) continue;
      const sd = stateMap.get(stateName);
      stateDataPoints.push({
        cx: centroid[0], cy: centroid[1],
        name: stateName,
        totalKids: sd.totalKids,
        avgP1: sd.avgP1,
      });
    }

    // Radius scale
    const maxKids = d3.max(stateDataPoints, d => d.totalKids);
    const rScale = d3.scaleSqrt().domain([0, maxKids]).range([4, W * 0.075]);

    // Draw bubbles
    const bubbleG = svg.append('g').attr('class', 'bubbles');
    bubbleG.selectAll('circle')
      .data(stateDataPoints)
      .join('circle')
      .attr('cx', d => d.cx)
      .attr('cy', d => d.cy)
      .attr('r',  d => rScale(d.totalKids))
      .attr('fill', d => bubbleColor(d.avgP1))
      .attr('fill-opacity', 0.7)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseenter', function(ev, d) {
        d3.select(this).attr('fill-opacity', 0.92).attr('stroke', '#333').attr('stroke-width', 2);
        const rect = bubbleSvgEl.getBoundingClientRect();
        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top  - 10,
          name:  d.name,
          state: '',
          p1:    d.avgP1,
          kids:  d.totalKids,
          isBubble: true,
        };
      })
      .on('mousemove', function(ev) {
        const rect = bubbleSvgEl.getBoundingClientRect();
        tooltip = { ...tooltip,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top  - 10 };
      })
      .on('mouseleave', function() {
        d3.select(this).attr('fill-opacity', 0.7).attr('stroke', '#fff').attr('stroke-width', 1);
        tooltip = { ...tooltip, visible: false };
      });

    // Legend (color)
    const lg = [
      { c: '#C0392B', l: 'Stuck (< 40th pctile)'   },
      { c: '#D4A017', l: 'Treading water (40–50th)' },
      { c: '#2471A3', l: 'Climbing (> 50th pctile)' },
    ];
    const lG = svg.append('g').attr('transform', `translate(10,${H - 80})`);
    lg.forEach((item, i) => {
      lG.append('circle').attr('cx',5).attr('cy',i*17+5).attr('r',5).attr('fill',item.c).attr('fill-opacity',0.8);
      lG.append('text').attr('x',16).attr('y',i*17+9.5).attr('font-size',10).attr('fill','#444').text(item.l);
    });

    // Bubble size legend
    const sizeLG = svg.append('g').attr('transform', `translate(10,${H - 18})`);
    sizeLG.append('text').attr('x',0).attr('y',0).attr('font-size',10).attr('fill','#888')
      .text('Bubble size = # children from low-income families');
  }

  $effect(() => { if (!mapLoading && viewMode === 'map') drawMap(mapStep); });
  $effect(() => { if (!mapLoading && viewMode === 'bubble' && bubbleSvgEl) drawBubbleMap(); });

  onMount(async () => {
    const [rawData, us] = await Promise.all([
      fetch(`${base}/data/data.json`).then(r => r.json()),
      fetch(`${base}/data/counties-10m.json`).then(r => r.json()),
    ]);
    countyMap  = preprocess(rawData);
    geoData    = us;
    mapLoading = false;
  });
</script>

<div class="map-wrap">
  {#if mapLoading}
    <p class="map-loading">Loading map…</p>
  {:else}
    View toggle 
    <div class="view-toggle">
      <button class:active={viewMode === 'map'} onclick={() => viewMode = 'map'}>
        County map
      </button>
      <button class:active={viewMode === 'bubble'} onclick={() => viewMode = 'bubble'}>
        State bubbles
      </button>
    </div>

    {#if viewMode === 'map'}
      <svg bind:this={svgEl} style="width:100%;display:block;"></svg>
    {:else}
      <svg bind:this={bubbleSvgEl} style="width:100%;display:block;"></svg>
    {/if}

    {#if tooltip.visible}
      <div class="tooltip" style="left:{tooltip.x}px;top:{tooltip.y}px">
        {#if tooltip.isBubble}
          <strong>{tooltip.name}</strong><br/>
          Avg. poor kids' adult rank:
          <strong style="color:{
            tooltip.p1 == null      ? '#aaa'     :
            tooltip.p1 < THRESHOLD_LO  ? '#C0392B' :
            tooltip.p1 <= THRESHOLD_HI ? '#D4A017' : '#2471A3'
          }">
            {tooltip.p1 != null ? tooltip.p1.toFixed(1) + 'th percentile' : 'no data'}
          </strong><br/>
          Children counted: <strong>{tooltip.kids?.toLocaleString()}</strong>
        {:else}
          <strong>{tooltip.name}, {tooltip.state}</strong><br/>
          Poor kids' adult rank:
          <strong style="color:{
            tooltip.p1 == null      ? '#aaa'     :
            tooltip.p1 < THRESHOLD_LO  ? '#C0392B' :
            tooltip.p1 <= THRESHOLD_HI ? '#777'    : '#2471A3'
          }">
            {tooltip.p1 != null ? tooltip.p1.toFixed(1) + 'th percentile' : 'no data'}
          </strong>
        {/if}
      </div>
    {/if}

    <Progress dots 
    <div class="step-dots">
      {#each [{s:1,c:'#C0392B'},{s:2,c:'#D4A017'},{s:3,c:'#2471A3'}] as d}
        <div class="dot" class:active={mapStep >= d.s} style="--c:{d.c}"></div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .map-wrap {
    position: relative;
    width: 100%;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 16px rgba(0,0,0,.08);
  }
  .map-loading { color: #aaa; font-size: 1rem; padding: 2rem; text-align: center; }

  /* ── View toggle ── */
  .view-toggle {
    display: flex;
    gap: 0;
    background: #f5f5f5;
    border-bottom: 1px solid #e0e0e0;
  }
  .view-toggle button {
    flex: 1;
    padding: 7px 0;
    font-size: 12px;
    font-weight: 500;
    color: #777;
    background: transparent;
    border: none;
    cursor: pointer;
    transition: background .2s, color .2s;
    letter-spacing: 0.02em;
  }
  .view-toggle button.active {
    background: #fff;
    color: #2c3e50;
    box-shadow: inset 0 -2px 0 #2471A3;
  }
  .view-toggle button:hover:not(.active) {
    background: #ebebeb;
    color: #444;
  }

  .step-dots {
    display: flex;
    justify-content: center;
    gap: 10px;
    padding: 8px 0;
    background: #fff;
  }
  .dot {
    width: 9px; height: 9px;
    border-radius: 50%;
    background: #ddd;
    transition: background .4s, transform .3s;
  }
  .dot.active { background: var(--c); transform: scale(1.3); }

  .tooltip {
    position: absolute;
    background: rgba(15,15,15,.9);
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
</style> --> 


<!-- <script module>
  export const THRESHOLD_LO = 40;
  export const THRESHOLD_HI = 50;

  export const STEPS = [
    {
      id: 0,
      title: "The Geographic Lottery",
      content: "For children born into low-income families, their adult economic success is highly dependent on their specific county of birth. Why does a zip code matter so much in the U.S.?",
    },
    {
      id: 1,
      title: "Most stay stuck.",
      content: "In the majority of U.S. counties, children born into the poorest families reach only the 25th–40th income percentile as adults.",
      statNum: "~60%",
      statLabel: "of counties leave poor kids below the 40th percentile",
      statColor: "#C0392B"
    },
    {
      id: 2,
      title: "Some tread water.",
      content: "A smaller share of counties land near the middle — children reaching roughly the 40th–50th percentile.",
      statNum: "~20%",
      statLabel: "of counties produce outcomes near the national median",
      statColor: "#D4A017"
    },
    {
      id: 3,
      title: "Very few actually climb.",
      content: "Only in a minority of counties — concentrated in the Upper Midwest — do poor kids consistently exceed the 50th percentile.",
      statNum: "~20%",
      statLabel: "of counties enable real upward mobility",
      statColor: "#2471A3"
    },
  ];
</script>

<script>
  import { onMount, onDestroy } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';
  import * as topojson from 'topojson-client';

  let { mapStep = $bindable(0) } = $props();

  let svgEl        = $state(null);
  let bubbleSvgEl  = $state(null);
  let dorlingEl    = $state(null);
  let mapLoading   = $state(true);
  let tooltip      = $state({ visible: false, x: 0, y: 0, name: '', p1: null, kids: null, isBubble: false });
  let viewMode     = $state('map'); // 'map' | 'bubble' | 'dorling'

  let countyMap = new Map();
  let stateMap  = new Map();
  let geoData   = null;
  let dorlingSim = null; // keep reference to stop old simulation

  // ── Colour helpers ──
  function mobility(p1) {
    if (p1 == null) return 'none';
    if (p1 < THRESHOLD_LO)       return 'stuck';
    if (p1 <= THRESHOLD_HI)      return 'water';
    return 'climb';
  }
  const COLORS = { stuck: '#C0392B', water: '#D4A017', climb: '#2471A3', none: '#e8e8e8' };

  function countyFill(p1, step) {
    const m = mobility(p1);
    if (m === 'none') return '#e8e8e8';
    if (m === 'stuck'  && step < 1) return '#e8e8e8';
    if (m === 'water'  && step < 2) return '#e8e8e8';
    if (m === 'climb'  && step < 3) return '#e8e8e8';
    return COLORS[m];
  }

  // ── Preprocess ──
  function preprocess(raw) {
    const m = new Map();
    const stateAgg = new Map();
    for (const row of raw) {
      if (!row.fips) continue;
      const v = row['kfr_pooled_pooled_p1_1978'];
      if (v == null) continue;
      const p1   = +v * 100;
      const kids = +(row['count_pooled_pooled_p1_1978'] ?? row['n'] ?? 1000);
      m.set(row.fips, { name: row.county_name ?? 'Unknown', state: row.state_name ?? '', p1, kids });
      const st = row.state_name ?? 'Unknown';
      if (!stateAgg.has(st)) stateAgg.set(st, { totalKids: 0, weightedP1: 0 });
      const s = stateAgg.get(st);
      s.totalKids  += kids;
      s.weightedP1 += p1 * kids;
    }
    for (const [st, agg] of stateAgg) {
      stateMap.set(st, {
        name: st,
        totalKids: agg.totalKids,
        avgP1: agg.totalKids > 0 ? agg.weightedP1 / agg.totalKids : null,
      });
    }
    return m;
  }

  // ── Build state centroid lookup from topojson ──
  function buildStateCentroids(geoData, proj) {
    const states   = topojson.feature(geoData, geoData.objects.states);
    const pathGen  = d3.geoPath(proj);
    const result   = [];
    for (const feat of states.features) {
      const centroid = pathGen.centroid(feat);
      if (!centroid || isNaN(centroid[0])) continue;
      // Map numeric FIPS → state name via countyMap
      const stateFips = String(feat.id).padStart(2, '0');
      let stateName = null;
      for (const [fips, county] of countyMap) {
        if (String(fips).padStart(5, '0').startsWith(stateFips)) {
          stateName = county.state;
          break;
        }
      }
      if (!stateName || !stateMap.has(stateName)) continue;
      const sd = stateMap.get(stateName);
      result.push({
        id: feat.id,
        name: stateName,
        x0: centroid[0],   // geographic centroid (anchor)
        y0: centroid[1],
        x: centroid[0],    // simulation position
        y: centroid[1],
        totalKids: sd.totalKids,
        avgP1: sd.avgP1,
      });
    }
    return result;
  }

  // ── Draw choropleth map ──
  function drawMap(step) {
    if (!svgEl || !geoData || countyMap.size === 0) return;

    const existing = d3.select(svgEl).select('g.counties');
    if (!existing.empty()) {
      existing.selectAll('path.county')
        .transition().duration(1200).ease(d3.easeCubicInOut)
        .attr('fill', d => countyFill(countyMap.get(d.id)?.p1 ?? null, step));
      return;
    }

    const W = svgEl.clientWidth || 600;
    const H = Math.round(W * 0.62);
    const svg = d3.select(svgEl);
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const counties = topojson.feature(geoData, geoData.objects.counties);
    const proj = d3.geoAlbersUsa().fitSize([W, H], counties);
    const path = d3.geoPath(proj);
    const g = svg.append('g').attr('class', 'counties');

    g.selectAll('path.county')
      .data(counties.features)
      .join('path')
      .attr('class', 'county')
      .attr('d', path)
      .attr('fill', d => countyFill(countyMap.get(d.id)?.p1 ?? null, step))
      .attr('stroke', '#fff').attr('stroke-width', 0.25)
      .on('mouseenter', function(ev, d) {
        d3.select(this).raise().attr('stroke', '#333').attr('stroke-width', 1.5);
        const c   = countyMap.get(d.id);
        const rect = svgEl.getBoundingClientRect();
        tooltip = { visible: true, x: ev.clientX - rect.left + 12, y: ev.clientY - rect.top - 10,
          name: c?.name ?? 'Unknown', state: c?.state ?? '', p1: c?.p1 ?? null, isBubble: false };
      })
      .on('mousemove', function(ev) {
        const rect = svgEl.getBoundingClientRect();
        tooltip = { ...tooltip, x: ev.clientX - rect.left + 12, y: ev.clientY - rect.top - 10 };
      })
      .on('mouseleave', function() {
        d3.select(this).attr('stroke', '#fff').attr('stroke-width', 0.25);
        tooltip = { ...tooltip, visible: false };
      });

    svg.append('path')
      .datum(topojson.mesh(geoData, geoData.objects.states, (a, b) => a !== b))
      .attr('d', path).attr('fill', 'none').attr('stroke', '#fff').attr('stroke-width', 0.9);

    const lg = [
      { c: '#C0392B', l: 'Stuck (< 40th pctile)'   },
      { c: '#D4A017', l: 'Treading water (40–50th)' },
      { c: '#2471A3', l: 'Climbing (> 50th pctile)' },
    ];
    const lG = svg.append('g').attr('transform', `translate(10,${H - 54})`);
    lg.forEach((item, i) => {
      lG.append('rect').attr('x', 0).attr('y', i * 17).attr('width', 11).attr('height', 11).attr('rx', 2).attr('fill', item.c);
      lG.append('text').attr('x', 16).attr('y', i * 17 + 9.5).attr('font-size', 10).attr('fill', '#555').text(item.l);
    });
  }

  // ── Draw Dorling cartogram ──
  function drawDorling() {
    if (!dorlingEl || !geoData || stateMap.size === 0) return;

    // Stop any previous simulation
    if (dorlingSim) { dorlingSim.stop(); dorlingSim = null; }

    const W = dorlingEl.clientWidth || 600;
    const H = Math.round(W * 0.62);
    const svg = d3.select(dorlingEl);
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    // Build projection (use counties for accurate fit)
    const counties  = topojson.feature(geoData, geoData.objects.counties);
    const proj      = d3.geoAlbersUsa().fitSize([W, H], counties);

    // State centroids + data
    const nodes = buildStateCentroids(geoData, proj);

    // Radius scale (sqrt so area ∝ children count)
    const maxKids = d3.max(nodes, d => d.totalKids);
    const rScale  = d3.scaleSqrt().domain([0, maxKids]).range([0, W * 0.072]);

    // ── Force simulation ──
    // - forceCollide: prevent overlap with small padding
    // - custom anchor force: pull each node back toward its geographic centroid
    const anchorStrength = 0.18;

    dorlingSim = d3.forceSimulation(nodes)
      .force('collide', d3.forceCollide(d => rScale(d.totalKids) + 1.5).strength(0.85).iterations(4))
      .force('anchor', () => {
        for (const d of nodes) {
          d.vx += (d.x0 - d.x) * anchorStrength;
          d.vy += (d.y0 - d.y) * anchorStrength;
        }
      })
      .alphaDecay(0.02)
      .stop();

    // Run simulation synchronously for 200 ticks (no animation lag)
    for (let i = 0; i < 200; i++) dorlingSim.tick();

    // ── Draw faint state outlines for geographic reference ──
    const statesFeature = topojson.feature(geoData, geoData.objects.states);
    const pathGen = d3.geoPath(proj);
    svg.append('g')
      .selectAll('path')
      .data(statesFeature.features)
      .join('path')
      .attr('d', pathGen)
      .attr('fill', '#f5f5f5')
      .attr('stroke', '#ddd')
      .attr('stroke-width', 0.6);

    // ── Draw connector lines from centroid to bubble (if displaced) ──
    const leaderG = svg.append('g').attr('class', 'leaders');
    leaderG.selectAll('line')
      .data(nodes)
      .join('line')
      .attr('x1', d => d.x0).attr('y1', d => d.y0)
      .attr('x2', d => d.x).attr('y2', d => d.y)
      .attr('stroke', '#bbb')
      .attr('stroke-width', 0.7)
      .attr('stroke-dasharray', '2 2')
      // Only show if displaced more than 8px
      .attr('opacity', d => {
        const dist = Math.hypot(d.x - d.x0, d.y - d.y0);
        return dist > 8 ? 0.6 : 0;
      });

    // ── Draw circles ──
    const circleG = svg.append('g').attr('class', 'dorling-circles');
    const circles = circleG.selectAll('g.state-circle')
      .data(nodes)
      .join('g')
      .attr('class', 'state-circle')
      .attr('transform', d => `translate(${d.x},${d.y})`)
      .style('cursor', 'pointer');

    // Shadow ring for depth
    circles.append('circle')
      .attr('r', d => rScale(d.totalKids) + 1.5)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(0,0,0,0.07)')
      .attr('stroke-width', 3);

    // Main fill circle
    circles.append('circle')
      .attr('r', d => rScale(d.totalKids))
      .attr('fill', d => COLORS[mobility(d.avgP1)] ?? '#aaa')
      .attr('fill-opacity', 0.82)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.2);

    // State abbreviation label (only if circle is large enough)
    const stateAbbr = getStateAbbreviations();
    circles.filter(d => rScale(d.totalKids) >= 14)
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', d => Math.min(13, rScale(d.totalKids) * 0.55))
      .attr('font-weight', '600')
      .attr('fill', '#fff')
      .attr('pointer-events', 'none')
      .text(d => stateAbbr[d.name] ?? '');

    // Hover interaction
    circles
      .on('mouseenter', function(ev, d) {
        d3.select(this).select('circle:nth-child(2)')
          .attr('fill-opacity', 1)
          .attr('stroke', '#333')
          .attr('stroke-width', 2);
        const rect = dorlingEl.getBoundingClientRect();
        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top - 10,
          name: d.name,
          p1: d.avgP1,
          kids: d.totalKids,
          isBubble: true,
        };
      })
      .on('mousemove', function(ev) {
        const rect = dorlingEl.getBoundingClientRect();
        tooltip = { ...tooltip, x: ev.clientX - rect.left + 12, y: ev.clientY - rect.top - 10 };
      })
      .on('mouseleave', function() {
        d3.select(this).select('circle:nth-child(2)')
          .attr('fill-opacity', 0.82)
          .attr('stroke', '#fff')
          .attr('stroke-width', 1.2);
        tooltip = { ...tooltip, visible: false };
      });

    // ── Legend ──
    const lg = [
      { c: '#C0392B', l: 'Stuck (avg < 40th pctile)'   },
      { c: '#D4A017', l: 'Treading water (40–50th)'     },
      { c: '#2471A3', l: 'Climbing (avg > 50th pctile)' },
    ];
    const lG = svg.append('g').attr('transform', `translate(10,${H - 72})`);
    lg.forEach((item, i) => {
      lG.append('circle').attr('cx', 5).attr('cy', i * 17 + 5).attr('r', 5).attr('fill', item.c).attr('fill-opacity', 0.85);
      lG.append('text').attr('x', 16).attr('y', i * 17 + 9.5).attr('font-size', 10).attr('fill', '#555').text(item.l);
    });
    lG.append('text').attr('x', 0).attr('y', 57).attr('font-size', 9.5).attr('fill', '#888')
      .text('Circle size = # children from low-income families (state total)');
  }

  // ── State name → 2-letter abbreviation ──
  function getStateAbbreviations() {
    return {
      'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
      'Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA',
      'Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA',
      'Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD',
      'Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS','Missouri':'MO',
      'Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ',
      'New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH',
      'Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC',
      'South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT',
      'Virginia':'VA','Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY',
      'District of Columbia':'DC',
    };
  }

  // ── Reactive effects ──
  $effect(() => { if (!mapLoading && viewMode === 'map') drawMap(mapStep); });
  $effect(() => { if (!mapLoading && viewMode === 'dorling' && dorlingEl) drawDorling(); });

  onMount(async () => {
    const [rawData, us] = await Promise.all([
      fetch(`${base}/data/data.json`).then(r => r.json()),
      fetch(`${base}/data/counties-10m.json`).then(r => r.json()),
    ]);
    countyMap = preprocess(rawData);
    geoData   = us;
    mapLoading = false;
  });

  onDestroy(() => { if (dorlingSim) dorlingSim.stop(); });
</script>

<div class="map-wrap">
  {#if mapLoading}
    <p class="map-loading">Loading map…</p>
  {:else}

     Tab switcher 
    <div class="view-toggle">
      <button class:active={viewMode === 'map'}     onclick={() => viewMode = 'map'}>County map</button>
      <button class:active={viewMode === 'dorling'} onclick={() => viewMode = 'dorling'}>Dorling cartogram</button>
    </div>

    <!-- Views 
    {#if viewMode === 'map'}
      <svg bind:this={svgEl} style="width:100%;display:block;"></svg>
    {:else if viewMode === 'dorling'}
      <div class="dorling-label">Each circle = one state · size = children from low-income families</div>
      <svg bind:this={dorlingEl} style="width:100%;display:block;"></svg>
    {/if}

    <!-- Shared tooltip 
    {#if tooltip.visible}
      <div class="tooltip" style="left:{tooltip.x}px;top:{tooltip.y}px">
        {#if tooltip.isBubble}
          <strong>{tooltip.name}</strong><br/>
          Avg. mobility outcome:
          <strong style="color:{
            tooltip.p1 == null           ? '#aaa'     :
            tooltip.p1 < THRESHOLD_LO   ? '#C0392B'  :
            tooltip.p1 <= THRESHOLD_HI  ? '#D4A017'  : '#2471A3'
          }">
            {tooltip.p1 != null ? tooltip.p1.toFixed(1) + 'th percentile' : 'no data'}
          </strong><br/>
          Children counted: <strong>{tooltip.kids?.toLocaleString()}</strong>
        {:else}
          <strong>{tooltip.name}, {tooltip.state}</strong><br/>
          Poor kids' adult rank:
          <strong style="color:{
            tooltip.p1 == null           ? '#aaa'     :
            tooltip.p1 < THRESHOLD_LO   ? '#C0392B'  :
            tooltip.p1 <= THRESHOLD_HI  ? '#D4A017'  : '#2471A3'
          }">
            {tooltip.p1 != null ? tooltip.p1.toFixed(1) + 'th percentile' : 'no data'}
          </strong>
        {/if}
      </div>
    {/if}

    <!-- Progress dots (map view only) 
    {#if viewMode === 'map'}
      <div class="step-dots">
        {#each [{s:1,c:'#C0392B'},{s:2,c:'#D4A017'},{s:3,c:'#2471A3'}] as d}
          <div class="dot" class:active={mapStep >= d.s} style="--c:{d.c}"></div>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .map-wrap {
    position: relative;
    width: 100%;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 16px rgba(0,0,0,.08);
    background: #fff;
  }
  .map-loading { color: #aaa; font-size: 1rem; padding: 2rem; text-align: center; }

  .view-toggle {
    display: flex;
    background: #f5f5f5;
    border-bottom: 1px solid #e0e0e0;
  }
  .view-toggle button {
    flex: 1;
    padding: 8px 0;
    font-size: 12px;
    font-weight: 500;
    color: #888;
    background: transparent;
    border: none;
    cursor: pointer;
    transition: background .2s, color .2s;
    letter-spacing: 0.02em;
  }
  .view-toggle button.active {
    background: #fff;
    color: #2c3e50;
    box-shadow: inset 0 -2px 0 #2471A3;
  }
  .view-toggle button:hover:not(.active) {
    background: #ebebeb;
    color: #444;
  }

  .dorling-label {
    font-size: 11px;
    color: #888;
    text-align: center;
    padding: 5px 0 2px;
    background: #fff;
    letter-spacing: 0.01em;
  }

  .step-dots {
    display: flex;
    justify-content: center;
    gap: 10px;
    padding: 8px 0;
    background: #fff;
  }
  .dot {
    width: 9px; height: 9px;
    border-radius: 50%;
    background: #ddd;
    transition: background .4s, transform .3s;
  }
  .dot.active { background: var(--c); transform: scale(1.3); }

  .tooltip {
    position: absolute;
    background: rgba(15,15,15,.9);
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
</style> -->



<!-- <script module>
  export const THRESHOLD_LO = 40;
  export const THRESHOLD_HI = 50;

  export const STEPS = [
    {
      id: 0,
      title: "The Geographic Lottery",
      content: "For children born into low-income families, their adult economic success is highly dependent on their specific county of birth. Why does a zip code matter so much in the U.S.?",
    },
    {
      id: 1,
      title: "Most stay stuck.",
      content: "In the majority of U.S. counties, children born into the poorest families reach only the 25th–40th income percentile as adults.",
      statNum: "~60%",
      statLabel: "of counties leave poor kids below the 40th percentile",
      statColor: "#C0392B"
    },
    {
      id: 2,
      title: "Some tread water.",
      content: "A smaller share of counties land near the middle — children reaching roughly the 40th–50th percentile.",
      statNum: "~20%",
      statLabel: "of counties produce outcomes near the national median",
      statColor: "#D4A017"
    },
    {
      id: 3,
      title: "Very few actually climb.",
      content: "Only in a minority of counties — concentrated in the Upper Midwest — do poor kids consistently exceed the 50th percentile.",
      statNum: "~20%",
      statLabel: "of counties enable real upward mobility",
      statColor: "#2471A3"
    },
  ];
</script>

<script>
  import { onMount, onDestroy } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';
  import * as topojson from 'topojson-client';

  let { mapStep = $bindable(0) } = $props();

  let svgEl       = $state(null);
  let dorlingEl   = $state(null);
  let mapLoading  = $state(true);
  let tooltip     = $state({ visible: false, x: 0, y: 0, name: '', p1: null, kids: null, isBubble: false });
  let viewMode    = $state('map'); // 'map' | 'bubble'

  // Zoom state
  let zoomedState = $state(null); // null = national view, string = state name

  let countyMap = new Map();
  let stateMap  = new Map();
  let geoData   = null;
  let dorlingSim = null;

  // ── Colour helpers ──
  function mobility(p1) {
    if (p1 == null) return 'none';
    if (p1 < THRESHOLD_LO)  return 'stuck';
    if (p1 <= THRESHOLD_HI) return 'water';
    return 'climb';
  }
  const COLORS = { stuck: '#C0392B', water: '#D4A017', climb: '#2471A3', none: '#e8e8e8' };

  function countyFill(p1, step) {
    const m = mobility(p1);
    if (m === 'none')  return '#e8e8e8';
    if (m === 'stuck'  && step < 1) return '#e8e8e8';
    if (m === 'water'  && step < 2) return '#e8e8e8';
    if (m === 'climb'  && step < 3) return '#e8e8e8';
    return COLORS[m];
  }

  // ── Preprocess ──
  function preprocess(raw) {
    const m = new Map();
    const stateAgg = new Map();
    for (const row of raw) {
      if (!row.fips) continue;
      const v = row['kfr_pooled_pooled_p1_1978'];
      if (v == null) continue;
      const p1   = +v * 100;
      const kids = +(row['count_pooled_pooled_p1_1978'] ?? row['n'] ?? 1000);
      m.set(row.fips, { name: row.county_name ?? 'Unknown', state: row.state_name ?? '', p1, kids });
      const st = row.state_name ?? 'Unknown';
      if (!stateAgg.has(st)) stateAgg.set(st, { totalKids: 0, weightedP1: 0 });
      const s = stateAgg.get(st);
      s.totalKids  += kids;
      s.weightedP1 += p1 * kids;
    }
    for (const [st, agg] of stateAgg) {
      stateMap.set(st, {
        name: st,
        totalKids: agg.totalKids,
        avgP1: agg.totalKids > 0 ? agg.weightedP1 / agg.totalKids : null,
      });
    }
    return m;
  }

  // ── Get state name from FIPS prefix ──
  function getStateNameFromFips(stateFips) {
    for (const [fips, county] of countyMap) {
      if (String(fips).padStart(5, '0').startsWith(stateFips)) {
        return county.state;
      }
    }
    return null;
  }

  // ── Draw map (national or zoomed-in state) ──
  function drawMap(step) {
    if (!svgEl || !geoData || countyMap.size === 0) return;

    const W = svgEl.clientWidth || 600;
    const H = Math.round(W * 0.62);
    const svg = d3.select(svgEl);
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const allCounties = topojson.feature(geoData, geoData.objects.counties);
    const allStates   = topojson.feature(geoData, geoData.objects.states);

    // ── Filter to zoomed state if set ──
    let countyFeatures = allCounties.features;
    let stateFeature   = null;
    if (zoomedState) {
      // Find the state feature matching zoomedState
      stateFeature = allStates.features.find(f => {
        const sfips = String(f.id).padStart(2, '0');
        const name  = getStateNameFromFips(sfips);
        return name === zoomedState;
      });
      if (stateFeature) {
        const sfips = String(stateFeature.id).padStart(2, '0');
        countyFeatures = allCounties.features.filter(f =>
          String(f.id).padStart(5, '0').startsWith(sfips)
        );
      }
    }

    // ── Projection fitted to current view ──
    const fitTarget = stateFeature
      ? { type: 'FeatureCollection', features: countyFeatures }
      : allCounties;
    const proj = d3.geoAlbersUsa().fitSize([W, H], fitTarget);
    const path = d3.geoPath(proj);

    svg.selectAll('*').remove();

    // ── County fills ──
    const g = svg.append('g').attr('class', 'counties');
    g.selectAll('path.county')
      .data(countyFeatures)
      .join('path')
      .attr('class', 'county')
      .attr('d', path)
      .attr('fill', d => countyFill(countyMap.get(d.id)?.p1 ?? null, step))
      .attr('stroke', '#fff')
      .attr('stroke-width', zoomedState ? 0.5 : 0.25)
      .on('mouseenter', function(ev, d) {
        d3.select(this).raise().attr('stroke', '#333').attr('stroke-width', 1.5);
        const c    = countyMap.get(d.id);
        const rect = svgEl.getBoundingClientRect();
        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top - 10,
          name: c?.name ?? 'Unknown',
          state: c?.state ?? '',
          p1: c?.p1 ?? null,
          isBubble: false
        };
      })
      .on('mousemove', function(ev) {
        const rect = svgEl.getBoundingClientRect();
        tooltip = { ...tooltip, x: ev.clientX - rect.left + 12, y: ev.clientY - rect.top - 10 };
      })
      .on('mouseleave', function() {
        d3.select(this).attr('stroke', '#fff').attr('stroke-width', zoomedState ? 0.5 : 0.25);
        tooltip = { ...tooltip, visible: false };
      });

    // ── State borders ──
    if (zoomedState) {
      // Just the single state outline
      if (stateFeature) {
        svg.append('path')
          .datum(stateFeature)
          .attr('d', path)
          .attr('fill', 'none')
          .attr('stroke', '#555')
          .attr('stroke-width', 1.5);
      }
    } else {
      // All state borders
      svg.append('path')
        .datum(topojson.mesh(geoData, geoData.objects.states, (a, b) => a !== b))
        .attr('d', path)
        .attr('fill', 'none')
        .attr('stroke', '#fff')
        .attr('stroke-width', 0.9);

      // ── Proportional symbol overlay (national view only) ──
      const maxKids = d3.max([...stateMap.values()], d => d.totalKids);
      const rScale  = d3.scaleSqrt().domain([0, maxKids]).range([0, W * 0.055]);

      const bubbleData = [];
      for (const feat of allStates.features) {
        const centroid  = path.centroid(feat);
        if (!centroid || isNaN(centroid[0])) continue;
        const sfips     = String(feat.id).padStart(2, '0');
        const stateName = getStateNameFromFips(sfips);
        if (!stateName || !stateMap.has(stateName)) continue;
        const sd = stateMap.get(stateName);
        bubbleData.push({ feat, centroid, stateName, ...sd });
      }

      const bubbleG = svg.append('g').attr('class', 'state-bubbles');
      bubbleG.selectAll('circle.state-bubble')
        .data(bubbleData)
        .join('circle')
        .attr('class', 'state-bubble')
        .attr('cx', d => d.centroid[0])
        .attr('cy', d => d.centroid[1])
        .attr('r',  d => rScale(d.totalKids))
        .attr('fill', d => {
          const c = COLORS[mobility(d.avgP1)] ?? '#aaa';
          return c;
        })
        .attr('fill-opacity', 0.45)
        .attr('stroke', d => COLORS[mobility(d.avgP1)] ?? '#aaa')
        .attr('stroke-width', 1.2)
        .attr('stroke-opacity', 0.8)
        .style('cursor', 'pointer')
        .on('mouseenter', function(ev, d) {
          d3.select(this).attr('fill-opacity', 0.7).attr('stroke-width', 2);
          const rect = svgEl.getBoundingClientRect();
          tooltip = {
            visible: true,
            x: ev.clientX - rect.left + 12,
            y: ev.clientY - rect.top - 10,
            name: d.stateName,
            p1: d.avgP1,
            kids: d.totalKids,
            isBubble: true,
            isState: true,
          };
        })
        .on('mousemove', function(ev) {
          const rect = svgEl.getBoundingClientRect();
          tooltip = { ...tooltip, x: ev.clientX - rect.left + 12, y: ev.clientY - rect.top - 10 };
        })
        .on('mouseleave', function() {
          d3.select(this).attr('fill-opacity', 0.45).attr('stroke-width', 1.2);
          tooltip = { ...tooltip, visible: false };
        })
        .on('click', function(ev, d) {
          ev.stopPropagation();
          tooltip = { ...tooltip, visible: false };
          zoomedState = d.stateName;
          drawMap(mapStep);
        });
    }

    // ── Legend ──
    const lg = [
      { c: '#C0392B', l: 'Stuck (< 40th pctile)'   },
      { c: '#D4A017', l: 'Treading water (40–50th)' },
      { c: '#2471A3', l: 'Climbing (> 50th pctile)' },
    ];
    const lG = svg.append('g').attr('transform', `translate(10,${H - 54})`);
    lg.forEach((item, i) => {
      lG.append('rect').attr('x', 0).attr('y', i * 17).attr('width', 11).attr('height', 11).attr('rx', 2).attr('fill', item.c);
      lG.append('text').attr('x', 16).attr('y', i * 17 + 9.5).attr('font-size', 10).attr('fill', '#555').text(item.l);
    });

    // ── Bubble size note (national view only) ──
    if (!zoomedState) {
      svg.append('text')
        .attr('x', 10).attr('y', H - 62)
        .attr('font-size', 9).attr('fill', '#888')
        .text('Circle size = # children from low-income families · click to zoom into a state');
    }
  }

  // ── Dorling cartogram (unchanged from original) ──
  function buildStateCentroids(geoData, proj) {
    const states  = topojson.feature(geoData, geoData.objects.states);
    const pathGen = d3.geoPath(proj);
    const result  = [];
    for (const feat of states.features) {
      const centroid = pathGen.centroid(feat);
      if (!centroid || isNaN(centroid[0])) continue;
      const stateFips = String(feat.id).padStart(2, '0');
      const stateName = getStateNameFromFips(stateFips);
      if (!stateName || !stateMap.has(stateName)) continue;
      const sd = stateMap.get(stateName);
      result.push({
        id: feat.id, name: stateName,
        x0: centroid[0], y0: centroid[1],
        x:  centroid[0], y:  centroid[1],
        totalKids: sd.totalKids, avgP1: sd.avgP1,
      });
    }
    return result;
  }

  function drawDorling() {
    if (!dorlingEl || !geoData || stateMap.size === 0) return;
    if (dorlingSim) { dorlingSim.stop(); dorlingSim = null; }

    const W = dorlingEl.clientWidth || 600;
    const H = Math.round(W * 0.62);
    const svg = d3.select(dorlingEl);
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${W} ${H}`);

    const counties = topojson.feature(geoData, geoData.objects.counties);
    const proj     = d3.geoAlbersUsa().fitSize([W, H], counties);
    const nodes    = buildStateCentroids(geoData, proj);
    const maxKids  = d3.max(nodes, d => d.totalKids);
    const rScale   = d3.scaleSqrt().domain([0, maxKids]).range([0, W * 0.072]);
    const anchorStrength = 0.18;

    dorlingSim = d3.forceSimulation(nodes)
      .force('collide', d3.forceCollide(d => rScale(d.totalKids) + 1.5).strength(0.85).iterations(4))
      .force('anchor', () => {
        for (const d of nodes) {
          d.vx += (d.x0 - d.x) * anchorStrength;
          d.vy += (d.y0 - d.y) * anchorStrength;
        }
      })
      .alphaDecay(0.02).stop();
    for (let i = 0; i < 200; i++) dorlingSim.tick();

    const statesFeature = topojson.feature(geoData, geoData.objects.states);
    const pathGen = d3.geoPath(proj);
    svg.append('g').selectAll('path').data(statesFeature.features).join('path')
      .attr('d', pathGen).attr('fill', '#f5f5f5').attr('stroke', '#ddd').attr('stroke-width', 0.6);

    svg.append('g').attr('class', 'leaders').selectAll('line').data(nodes).join('line')
      .attr('x1', d => d.x0).attr('y1', d => d.y0)
      .attr('x2', d => d.x).attr('y2', d => d.y)
      .attr('stroke', '#bbb').attr('stroke-width', 0.7).attr('stroke-dasharray', '2 2')
      .attr('opacity', d => Math.hypot(d.x - d.x0, d.y - d.y0) > 8 ? 0.6 : 0);

    const circles = svg.append('g').attr('class', 'dorling-circles')
      .selectAll('g.state-circle').data(nodes).join('g').attr('class', 'state-circle')
      .attr('transform', d => `translate(${d.x},${d.y})`).style('cursor', 'pointer');

    circles.append('circle').attr('r', d => rScale(d.totalKids) + 1.5)
      .attr('fill', 'none').attr('stroke', 'rgba(0,0,0,0.07)').attr('stroke-width', 3);
    circles.append('circle').attr('r', d => rScale(d.totalKids))
      .attr('fill', d => COLORS[mobility(d.avgP1)] ?? '#aaa')
      .attr('fill-opacity', 0.82).attr('stroke', '#fff').attr('stroke-width', 1.2);

    const stateAbbr = getStateAbbreviations();
    circles.filter(d => rScale(d.totalKids) >= 14).append('text')
      .attr('text-anchor', 'middle').attr('dominant-baseline', 'central')
      .attr('font-size', d => Math.min(13, rScale(d.totalKids) * 0.55))
      .attr('font-weight', '600').attr('fill', '#fff').attr('pointer-events', 'none')
      .text(d => stateAbbr[d.name] ?? '');

    circles
      .on('mouseenter', function(ev, d) {
        d3.select(this).select('circle:nth-child(2)').attr('fill-opacity', 1).attr('stroke', '#333').attr('stroke-width', 2);
        const rect = dorlingEl.getBoundingClientRect();
        tooltip = { visible: true, x: ev.clientX - rect.left + 12, y: ev.clientY - rect.top - 10,
          name: d.name, p1: d.avgP1, kids: d.totalKids, isBubble: true };
      })
      .on('mousemove', function(ev) {
        const rect = dorlingEl.getBoundingClientRect();
        tooltip = { ...tooltip, x: ev.clientX - rect.left + 12, y: ev.clientY - rect.top - 10 };
      })
      .on('mouseleave', function() {
        d3.select(this).select('circle:nth-child(2)').attr('fill-opacity', 0.82).attr('stroke', '#fff').attr('stroke-width', 1.2);
        tooltip = { ...tooltip, visible: false };
      });

    const lg = [
      { c: '#C0392B', l: 'Stuck (avg < 40th pctile)'   },
      { c: '#D4A017', l: 'Treading water (40–50th)'     },
      { c: '#2471A3', l: 'Climbing (avg > 50th pctile)' },
    ];
    const lG = svg.append('g').attr('transform', `translate(10,${H - 72})`);
    lg.forEach((item, i) => {
      lG.append('circle').attr('cx', 5).attr('cy', i * 17 + 5).attr('r', 5).attr('fill', item.c).attr('fill-opacity', 0.85);
      lG.append('text').attr('x', 16).attr('y', i * 17 + 9.5).attr('font-size', 10).attr('fill', '#555').text(item.l);
    });
    lG.append('text').attr('x', 0).attr('y', 57).attr('font-size', 9.5).attr('fill', '#888')
      .text('Circle size = # children from low-income families (state total)');
  }

  function getStateAbbreviations() {
    return {
      'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
      'Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA',
      'Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA',
      'Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD',
      'Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS','Missouri':'MO',
      'Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ',
      'New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH',
      'Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC',
      'South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT',
      'Virginia':'VA','Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY',
      'District of Columbia':'DC',
    };
  }

  // ── Reactive effects ──
  $effect(() => { if (!mapLoading && viewMode === 'map')     drawMap(mapStep); });
  $effect(() => { if (!mapLoading && viewMode === 'dorling' && dorlingEl) drawDorling(); });
  // Re-draw when zoom state changes
  $effect(() => { zoomedState; if (!mapLoading && viewMode === 'map') drawMap(mapStep); });

  onMount(async () => {
    const [rawData, us] = await Promise.all([
      fetch(`${base}/data/data.json`).then(r => r.json()),
      fetch(`${base}/data/counties-10m.json`).then(r => r.json()),
    ]);
    countyMap  = preprocess(rawData);
    geoData    = us;
    mapLoading = false;
  });

  onDestroy(() => { if (dorlingSim) dorlingSim.stop(); });
</script>

<div class="map-wrap">
  {#if mapLoading}
    <p class="map-loading">Loading map…</p>
  {:else}

    <!-- Tab switcher 
    <div class="view-toggle">
      <button class:active={viewMode === 'map'}
        onclick={() => { viewMode = 'map'; zoomedState = null; }}>
        County map
      </button>
      <button class:active={viewMode === 'bubble'}
        onclick={() => { viewMode = 'bubble'; zoomedState = null; }}>
        Dorling cartogram
      </button>
    </div>

    <!-- Zoomed-state back button 
    {#if viewMode === 'map' && zoomedState}
      <div class="zoom-bar">
        <button class="back-btn" onclick={() => { zoomedState = null; drawMap(mapStep); }}>
          ← Back to US
        </button>
        <span class="zoom-label">{zoomedState} — county view</span>
      </div>
    {/if}

    <!-- Views 
    {#if viewMode === 'map'}
      <svg bind:this={svgEl} style="width:100%;display:block;"></svg>
    {:else if viewMode === 'dorling'}
      <div class="dorling-label">Each circle = one state · size = children from low-income families</div>
      <svg bind:this={dorlingEl} style="width:100%;display:block;"></svg>
    {/if}

    <!-- Shared tooltip 
    {#if tooltip.visible}
      <div class="tooltip" style="left:{tooltip.x}px;top:{tooltip.y}px">
        {#if tooltip.isBubble}
          <strong>{tooltip.name}</strong><br/>
          Avg. mobility outcome:
          <strong style="color:{
            tooltip.p1 == null          ? '#aaa'    :
            tooltip.p1 < THRESHOLD_LO  ? '#C0392B' :
            tooltip.p1 <= THRESHOLD_HI ? '#D4A017' : '#2471A3'
          }">
            {tooltip.p1 != null ? tooltip.p1.toFixed(1) + 'th percentile' : 'no data'}
          </strong><br/>
          Children counted: <strong>{tooltip.kids?.toLocaleString()}</strong>
          {#if tooltip.isState}<br/><em style="font-size:11px;opacity:.7">Click to zoom in</em>{/if}
        {:else}
          <strong>{tooltip.name}, {tooltip.state}</strong><br/>
          Poor kids' adult rank:
          <strong style="color:{
            tooltip.p1 == null          ? '#aaa'    :
            tooltip.p1 < THRESHOLD_LO  ? '#C0392B' :
            tooltip.p1 <= THRESHOLD_HI ? '#D4A017' : '#2471A3'
          }">
            {tooltip.p1 != null ? tooltip.p1.toFixed(1) + 'th percentile' : 'no data'}
          </strong>
        {/if}
      </div>
    {/if}

    <!-- Progress dots (map view only) 
    {#if viewMode === 'map' && !zoomedState}
      <div class="step-dots">
        {#each [{s:1,c:'#C0392B'},{s:2,c:'#D4A017'},{s:3,c:'#2471A3'}] as d}
          <div class="dot" class:active={mapStep >= d.s} style="--c:{d.c}"></div>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .map-wrap {
    position: relative;
    width: 100%;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 16px rgba(0,0,0,.08);
    background: #fff;
  }
  .map-loading { color: #aaa; font-size: 1rem; padding: 2rem; text-align: center; }

  .view-toggle {
    display: flex;
    background: #f5f5f5;
    border-bottom: 1px solid #e0e0e0;
  }
  .view-toggle button {
    flex: 1;
    padding: 8px 0;
    font-size: 12px;
    font-weight: 500;
    color: #888;
    background: transparent;
    border: none;
    cursor: pointer;
    transition: background .2s, color .2s;
    letter-spacing: 0.02em;
  }
  .view-toggle button.active {
    background: #fff;
    color: #2c3e50;
    box-shadow: inset 0 -2px 0 #2471A3;
  }
  .view-toggle button:hover:not(.active) {
    background: #ebebeb;
    color: #444;
  }

  /* ── Zoom bar ── */
  .zoom-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 12px;
    background: #f0f4f8;
    border-bottom: 1px solid #dce4ec;
  }
  .back-btn {
    font-size: 12px;
    font-weight: 600;
    color: #2471A3;
    background: transparent;
    border: 1px solid #2471A3;
    border-radius: 5px;
    padding: 3px 10px;
    cursor: pointer;
    transition: background .15s, color .15s;
  }
  .back-btn:hover { background: #2471A3; color: #fff; }
  .zoom-label {
    font-size: 12px;
    color: #555;
    font-weight: 500;
  }

  .dorling-label {
    font-size: 11px;
    color: #888;
    text-align: center;
    padding: 5px 0 2px;
    background: #fff;
    letter-spacing: 0.01em;
  }

  .step-dots {
    display: flex;
    justify-content: center;
    gap: 10px;
    padding: 8px 0;
    background: #fff;
  }
  .dot {
    width: 9px; height: 9px;
    border-radius: 50%;
    background: #ddd;
    transition: background .4s, transform .3s;
  }
  .dot.active { background: var(--c); transform: scale(1.3); }

  .tooltip {
    position: absolute;
    background: rgba(15,15,15,.9);
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
</style> -->



<script module>
  export const THRESHOLD_LO = 40;
  export const THRESHOLD_HI = 50;

  export const STEPS = [
    {
      id: 0,
      title: "The Geographic Lottery",
      content:
        "For children born into low-income families, where they grow up strongly shapes where they end up. In the U.S., your county of birth can influence how far you can rise.",
    },
    {
      id: 1,
      title: "Most stay stuck",
      content:
        "In most counties, children born poor grow up to still be relatively poor (25th–40th percentile).",
      statNum: "~60%",
      statLabel: "of counties keep poor children below average",
      statColor: "#C0392B",
    },
    {
      id: 2,
      title: "Some reach the middle",
      content:
        "In some counties, children born poor end up around the middle of the income distribution (40th–50th percentile).",
      statNum: "~20%",
      statLabel: "of counties lead to average outcomes",
      statColor: "#D4A017",
    },
    {
      id: 3,
      title: "Very few move ahead",
      content:
        "In a small number of counties, children born poor rise above average (above the 50th percentile).",
      statNum: "~20%",
      statLabel: "of counties enable upward mobility",
      statColor: "#2471A3",
    },
  ];
</script>

<script>
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import * as d3 from "d3";
  import * as topojson from "topojson-client";

  let { mapStep = $bindable(0) } = $props();

  let svgEl = $state(null);
  let bubbleEl = $state(null);

  let mapLoading = $state(true);
  let viewMode = $state("map"); // 'map' | 'bubble'
  let zoomedState = $state(null);

  let tooltip = $state({
    visible: false,
    x: 0,
    y: 0,
    name: "",
    state: "",
    p1: null,
    kids: null,
    isBubble: false,
    isState: false,
  });

  let countyMap = new Map();
  let stateMap = new Map();
  let geoData = null;

  const COLORS = {
    stuck: "#C0392B",
    water: "#D4A017",
    climb: "#2471A3",
    none: "#e8e8e8",
  };

  function mobility(p1) {
    if (p1 == null) return "none";
    if (p1 < THRESHOLD_LO) return "stuck";
    if (p1 <= THRESHOLD_HI) return "water";
    return "climb";
  }

  function countyFill(p1, step) {
    const m = mobility(p1);
    if (m === "none") return "#e8e8e8";
    if (m === "stuck" && step < 1) return "#e8e8e8";
    if (m === "water" && step < 2) return "#e8e8e8";
    if (m === "climb" && step < 3) return "#e8e8e8";
    return COLORS[m];
  }

  function preprocess(raw) {
    const m = new Map();
    const stateAgg = new Map();

    for (const row of raw) {
      if (!row.fips) continue;

      const v = row["kfr_pooled_pooled_p1_1978"];
      if (v == null) continue;

      const fips = String(row.fips).padStart(5, "0");
      const p1 = +v * 100;
      const kids = +(row["count_pooled_pooled_p1_1978"] ?? row["n"] ?? 1000);
      const state = row.state_name ?? "Unknown";

      m.set(fips, {
        name: row.county_name ?? "Unknown",
        state,
        p1,
        kids,
      });

      if (!stateAgg.has(state)) {
        stateAgg.set(state, {
          totalKids: 0,
          weightedP1: 0,
        });
      }

      const s = stateAgg.get(state);
      s.totalKids += kids;
      s.weightedP1 += p1 * kids;
    }

    for (const [st, agg] of stateAgg) {
      stateMap.set(st, {
        name: st,
        totalKids: agg.totalKids,
        avgP1: agg.totalKids > 0 ? agg.weightedP1 / agg.totalKids : null,
      });
    }

    return m;
  }

  function getStateNameFromFips(stateFips) {
    for (const [fips, county] of countyMap) {
      if (String(fips).padStart(5, "0").startsWith(stateFips)) {
        return county.state;
      }
    }
    return null;
  }

  function drawMap(step) {
    if (!svgEl || !geoData || countyMap.size === 0) return;

    const W = svgEl.clientWidth || 600;
    const H = Math.round(W * 0.72);
    const svg = d3.select(svgEl);

    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${W} ${H}`);

    const allCounties = topojson.feature(geoData, geoData.objects.counties);
    const allStates = topojson.feature(geoData, geoData.objects.states);

    const proj = d3.geoAlbersUsa().fitSize([W, H], allCounties);
    const path = d3.geoPath(proj);

    svg
      .append("g")
      .attr("class", "counties")
      .selectAll("path.county")
      .data(allCounties.features)
      .join("path")
      .attr("class", "county")
      .attr("d", path)
      .attr("fill", (d) => countyFill(countyMap.get(String(d.id).padStart(5, "0"))?.p1 ?? null, step))
      .attr("stroke", "#fff")
      .attr("stroke-width", 0.25)
      .on("mouseenter", function (ev, d) {
        d3.select(this).raise().attr("stroke", "#333").attr("stroke-width", 1.5);

        const id = String(d.id).padStart(5, "0");
        const c = countyMap.get(id);
        const rect = svgEl.getBoundingClientRect();

        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top - 10,
          name: c?.name ?? "Unknown",
          state: c?.state ?? "",
          p1: c?.p1 ?? null,
          kids: c?.kids ?? null,
          isBubble: false,
          isState: false,
        };
      })
      .on("mousemove", function (ev) {
        const rect = svgEl.getBoundingClientRect();
        tooltip = {
          ...tooltip,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top - 10,
        };
      })
      .on("mouseleave", function () {
        d3.select(this).attr("stroke", "#fff").attr("stroke-width", 0.25);
        tooltip = { ...tooltip, visible: false };
      });

    svg
      .append("path")
      .datum(topojson.mesh(geoData, geoData.objects.states, (a, b) => a !== b))
      .attr("d", path)
      .attr("fill", "none")
      .attr("stroke", "#fff")
      .attr("stroke-width", 0.9);

    drawLegend(svg, H);

    const noteY = H - 50;

    svg
      .append("text")
      .attr("x", 16)
      .attr("y", noteY)
      .attr("font-size", 11)
      .attr("fill", "#777")
      .text("County color = adult income rank for children from low-income families");
  }

  function drawBubbleMap() {
    if (!bubbleEl || !geoData || stateMap.size === 0) return;

    const W = bubbleEl.clientWidth || 600;
    const H = Math.round(W * 0.72);
    const svg = d3.select(bubbleEl);

    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${W} ${H}`);

    const allCounties = topojson.feature(geoData, geoData.objects.counties);
    const allStates = topojson.feature(geoData, geoData.objects.states);

    let countyFeatures = allCounties.features;
    let stateFeature = null;

    if (zoomedState) {
      stateFeature = allStates.features.find((f) => {
        const sfips = String(f.id).padStart(2, "0");
        const name = getStateNameFromFips(sfips);
        return name === zoomedState;
      });

      if (stateFeature) {
        const sfips = String(stateFeature.id).padStart(2, "0");
        countyFeatures = allCounties.features.filter((f) =>
          String(f.id).padStart(5, "0").startsWith(sfips)
        );
      }
    }

    const fitTarget = stateFeature
      ? { type: "FeatureCollection", features: countyFeatures }
      : allCounties;

    //const proj = d3.geoAlbersUsa().fitSize([W, H], fitTarget);
    const bottomSpace = zoomedState ? 0 : 60;

    const proj = d3.geoAlbersUsa().fitExtent(
      [
        [20, 25],
        [W - 20, H - bottomSpace]
      ],
      fitTarget
    );
    const path = d3.geoPath(proj);

    svg
      .append("g")
      .attr("class", "counties")
      .selectAll("path.county")
      .data(countyFeatures)
      .join("path")
      .attr("class", "county")
      .attr("d", path)
      .attr("fill", (d) => {
        if (!zoomedState) return "#eeeeee";
        const id = String(d.id).padStart(5, "0");
        return countyFill(countyMap.get(id)?.p1 ?? null, 3);
      })
      .attr("stroke", "#fff")
      .attr("stroke-width", zoomedState ? 0.5 : 0.25)
      .on("mouseenter", function (ev, d) {
        if (!zoomedState) return;

        d3.select(this).raise().attr("stroke", "#333").attr("stroke-width", 1.5);

        const id = String(d.id).padStart(5, "0");
        const c = countyMap.get(id);
        const rect = bubbleEl.getBoundingClientRect();

        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top - 10,
          name: c?.name ?? "Unknown",
          state: c?.state ?? "",
          p1: c?.p1 ?? null,
          kids: c?.kids ?? null,
          isBubble: false,
          isState: false,
        };
      })
      .on("mousemove", function (ev) {
        const rect = bubbleEl.getBoundingClientRect();
        tooltip = {
          ...tooltip,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top - 10,
        };
      })
      .on("mouseleave", function () {
        d3.select(this)
          .attr("stroke", "#fff")
          .attr("stroke-width", zoomedState ? 0.5 : 0.25);
        tooltip = { ...tooltip, visible: false };
      });

    if (zoomedState) {
      if (stateFeature) {
        svg
          .append("path")
          .datum(stateFeature)
          .attr("d", path)
          .attr("fill", "none")
          .attr("stroke", "#555")
          .attr("stroke-width", 1.5);
      }

      drawLegend(svg, H);

      svg
        .append("text")
        .attr("x", 10)
        .attr("y", 18)
        .attr("font-size", 12)
        .attr("font-weight", 600)
        .attr("fill", "#444")
        .text(`${zoomedState} — county view`);

      return;
    }

    svg
      .append("path")
      .datum(topojson.mesh(geoData, geoData.objects.states, (a, b) => a !== b))
      .attr("d", path)
      .attr("fill", "none")
      .attr("stroke", "#fff")
      .attr("stroke-width", 0.9);

    const maxKids = d3.max([...stateMap.values()], (d) => d.totalKids);
    const rScale = d3.scaleSqrt().domain([0, maxKids]).range([0, W * 0.055]);

    const bubbleData = [];

    for (const feat of allStates.features) {
      const centroid = path.centroid(feat);
      if (!centroid || isNaN(centroid[0])) continue;

      const sfips = String(feat.id).padStart(2, "0");
      const stateName = getStateNameFromFips(sfips);

      if (!stateName || !stateMap.has(stateName)) continue;

      const sd = stateMap.get(stateName);
      bubbleData.push({
        feat,
        centroid,
        stateName,
        ...sd,
      });
    }

    svg
      .append("g")
      .attr("class", "state-bubbles")
      .selectAll("circle.state-bubble")
      .data(bubbleData)
      .join("circle")
      .attr("class", "state-bubble")
      .attr("cx", (d) => d.centroid[0])
      .attr("cy", (d) => d.centroid[1])
      .attr("r", (d) => rScale(d.totalKids))
      .attr("fill", (d) => COLORS[mobility(d.avgP1)] ?? "#aaa")
      .attr("fill-opacity", 0.55)
      .attr("stroke", (d) => COLORS[mobility(d.avgP1)] ?? "#aaa")
      .attr("stroke-width", 1.3)
      .attr("stroke-opacity", 0.85)
      .style("cursor", "pointer")
      .on("mouseenter", function (ev, d) {
        d3.select(this).attr("fill-opacity", 0.75).attr("stroke-width", 2);

        const rect = bubbleEl.getBoundingClientRect();

        tooltip = {
          visible: true,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top - 10,
          name: d.stateName,
          state: "",
          p1: d.avgP1,
          kids: d.totalKids,
          isBubble: true,
          isState: true,
        };
      })
      .on("mousemove", function (ev) {
        const rect = bubbleEl.getBoundingClientRect();
        tooltip = {
          ...tooltip,
          x: ev.clientX - rect.left + 12,
          y: ev.clientY - rect.top - 10,
        };
      })
      .on("mouseleave", function () {
        d3.select(this).attr("fill-opacity", 0.55).attr("stroke-width", 1.3);
        tooltip = { ...tooltip, visible: false };
      })
      .on("click", function (ev, d) {
        ev.stopPropagation();
        tooltip = { ...tooltip, visible: false };
        zoomedState = d.stateName;
        drawBubbleMap();
      });

    svg
      .append("text")
      .attr("x", 10)
      .attr("y", H - 55) //text y
      .attr("font-size", 9)
      .attr("fill", "#888")
      .text("Circle size = # children from low-income families · click a state circle to zoom in");

    drawLegend(svg, H);
  }

  function drawLegend(svg, H) {
    const lg = [
      { c: "#C0392B", l: "Stuck (< 40th pctile)" },
      { c: "#D4A017", l: "Treading water (40–50th)" },
      { c: "#2471A3", l: "Climbing (> 50th pctile)" },
    ];

    const lG = svg.append("g").attr("transform", `translate(16,${H -48})`);

    lg.forEach((item, i) => {
      lG
        .append("rect")
        .attr("x", 0)
        .attr("y", i * 17)
        .attr("width", 11)
        .attr("height", 11)
        .attr("rx", 2)
        .attr("fill", item.c);

      lG
        .append("text")
        .attr("x", 16)
        .attr("y", i * 17 + 9.5)
        .attr("font-size", 10)
        .attr("fill", "#555")
        .text(item.l);
    });
  }

  $effect(() => {
    if (!mapLoading && viewMode === "map") {
      zoomedState = null;
      drawMap(mapStep);
    }
  });

  $effect(() => {
    if (!mapLoading && viewMode === "bubble" && bubbleEl) {
      drawBubbleMap();
    }
  });

  $effect(() => {
    zoomedState;
    if (!mapLoading && viewMode === "bubble" && bubbleEl) {
      drawBubbleMap();
    }
  });

  onMount(async () => {
    const [rawData, us] = await Promise.all([
      fetch(`${base}/data/data.json`).then((r) => r.json()),
      fetch(`${base}/data/counties-10m.json`).then((r) => r.json()),
    ]);

    countyMap = preprocess(rawData);
    geoData = us;
    mapLoading = false;
  });
</script>

<div class="map-wrap">
  {#if mapLoading}
    <p class="map-loading">Loading map…</p>
  {:else}
    <div class="view-toggle">
      <button
        class:active={viewMode === "map"}
        onclick={() => {
          viewMode = "map";
          zoomedState = null;
        }}
      >
        County map
      </button>

      <button
        class:active={viewMode === "bubble"}
        onclick={() => {
          viewMode = "bubble";
          zoomedState = null;
        }}
      >
        State bubble map
      </button>
    </div>

    {#if viewMode === "bubble" && zoomedState}
      <div class="zoom-bar">
        <button
          class="back-btn"
          onclick={() => {
            zoomedState = null;
            drawBubbleMap();
          }}
        >
          ← Back to US
        </button>
        <span class="zoom-label">{zoomedState} — county view</span>
      </div>
    {/if}

    {#if viewMode === "map"}
      <svg bind:this={svgEl} style="width:100%;display:block;"></svg>
    {:else if viewMode === "bubble"}
      <svg bind:this={bubbleEl} style="width:100%;display:block;"></svg>
    {/if}

    {#if tooltip.visible}
      <div class="tooltip" style="left:{tooltip.x}px;top:{tooltip.y}px">
        {#if tooltip.isBubble}
          <strong>{tooltip.name}</strong><br />
          Avg. mobility outcome:
          <strong
            style="color:{
              tooltip.p1 == null
                ? '#aaa'
                : tooltip.p1 < THRESHOLD_LO
                  ? '#C0392B'
                  : tooltip.p1 <= THRESHOLD_HI
                    ? '#D4A017'
                    : '#2471A3'
            }"
          >
            {tooltip.p1 != null ? tooltip.p1.toFixed(1) + "th percentile" : "no data"}
          </strong><br />
          Children counted: <strong>{tooltip.kids?.toLocaleString()}</strong>
          {#if tooltip.isState}
            <br />
            <em style="font-size:11px;opacity:.7">Click to zoom in</em>
          {/if}
        {:else}
          <strong>{tooltip.name}, {tooltip.state}</strong><br />
          Poor kids' adult rank:
          <strong
            style="color:{
              tooltip.p1 == null
                ? '#aaa'
                : tooltip.p1 < THRESHOLD_LO
                  ? '#C0392B'
                  : tooltip.p1 <= THRESHOLD_HI
                    ? '#D4A017'
                    : '#2471A3'
            }"
          >
            {tooltip.p1 != null ? tooltip.p1.toFixed(1) + "th percentile" : "no data"}
          </strong>
        {/if}
      </div>
    {/if}

    {#if viewMode === "map"}
      <div class="step-dots">
        {#each [{ s: 1, c: "#C0392B" }, { s: 2, c: "#D4A017" }, { s: 3, c: "#2471A3" }] as d}
          <div class="dot" class:active={mapStep >= d.s} style="--c:{d.c}"></div>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .map-wrap {
    position: relative;
    width: 100%;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.08);
    background: #fff;
  }

  .map-loading {
    color: #aaa;
    font-size: 1rem;
    padding: 2rem;
    text-align: center;
  }

  .view-toggle {
    display: flex;
    background: #f5f5f5;
    border-bottom: 1px solid #e0e0e0;
  }

  .view-toggle button {
    flex: 1;
    padding: 8px 0;
    font-size: 12px;
    font-weight: 500;
    color: #888;
    background: transparent;
    border: none;
    cursor: pointer;
    transition:
      background 0.2s,
      color 0.2s;
    letter-spacing: 0.02em;
  }

  .view-toggle button.active {
    background: #fff;
    color: #2c3e50;
    box-shadow: inset 0 -2px 0 #2471a3;
  }

  .view-toggle button:hover:not(.active) {
    background: #ebebeb;
    color: #444;
  }

  .zoom-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 6px 12px;
    background: #f0f4f8;
    border-bottom: 1px solid #dce4ec;
  }

  .back-btn {
    font-size: 12px;
    font-weight: 600;
    color: #2471a3;
    background: transparent;
    border: 1px solid #2471a3;
    border-radius: 5px;
    padding: 3px 10px;
    cursor: pointer;
    transition:
      background 0.15s,
      color 0.15s;
  }

  .back-btn:hover {
    background: #2471a3;
    color: #fff;
  }

  .zoom-label {
    font-size: 12px;
    color: #555;
    font-weight: 500;
  }

  .step-dots {
    display: flex;
    justify-content: center;
    gap: 10px;
    padding: 8px 0;
    background: #fff;
  }

  .dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #ddd;
    transition:
      background 0.4s,
      transform 0.3s;
  }

  .dot.active {
    background: var(--c);
    transform: scale(1.3);
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
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    z-index: 10;

    
  }
</style>
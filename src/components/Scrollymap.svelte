<script module>
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
      statColor: "#888"
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
  import { base } from '$app/paths';

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
    else if (p1 <= THRESHOLD_HI) return step >= 2 ? '#999'    : '#e8e8e8';
    else                          return step >= 3 ? '#2471A3' : '#e8e8e8';
  }

  // ── Draw (first time) or recolor (subsequent steps) ──
  function drawMap(step) {
    if (!svgEl || !geoData || countyMap.size === 0) return;

    const existing = d3.select(svgEl).select('g.counties');
    if (!existing.empty()) {
      existing.selectAll('path.county')
        .transition().duration(600).ease(d3.easeCubicInOut)
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

<!-- ── Map SVG (place this in the right sticky column) ── -->
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

    <!-- Progress dots -->
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
</style>
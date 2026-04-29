<script>
  import { onMount, onDestroy } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';
  import * as topojson from 'topojson-client';

  let canvasEl = $state(null);
  let containerEl = $state(null);
  let isLoading = $state(true);
  let errorMsg = $state(null);
  let hover = $state({ visible: false, x: 0, y: 0, county: '', state: '', value: 0 });

  let deckInstance = null;
  let resizeObserver = null;

  async function init() {
    const [coreModule, layersModule] = await Promise.all([
      import('@deck.gl/core'),
      import('@deck.gl/layers'),
    ]);
    const { Deck, OrbitView, COORDINATE_SYSTEM, LightingEffect, AmbientLight, DirectionalLight } = coreModule;
    const { ColumnLayer, PathLayer } = layersModule;

    const [rawData, us] = await Promise.all([
      fetch(`${base}/data/data.json`).then((r) => r.json()),
      fetch(`${base}/data/counties-10m.json`).then((r) => r.json()),
    ]);

    const W = containerEl?.clientWidth || 800;
    const H = Math.max(500, Math.round(W * 0.62));

    const counties = topojson.feature(us, us.objects.counties);
    const states = topojson.feature(us, us.objects.states);

    // Project to pixel space, then re-center on the chart so OrbitView's
    // origin sits at the geographic center of the U.S.
    const projection = d3.geoAlbersUsa().fitSize([W, H], counties);

    const valueByFips = new Map();
    for (const d of rawData) {
      const v = +d.kfr_pooled_pooled_p1_1992;
      if (Number.isFinite(v)) valueByFips.set(d.fips, v);
    }

    const columns = [];
    for (const f of counties.features) {
      const fips = String(f.id).padStart(5, '0');
      const v = valueByFips.get(f.id) ?? valueByFips.get(fips);
      if (v == null) continue;
      const centroid = d3.geoCentroid(f);
      const xy = projection(centroid);
      if (!xy || !Number.isFinite(xy[0])) continue;
      const info = rawData.find((row) => row.fips === f.id || String(row.fips).padStart(5, '0') === fips);
      columns.push({
        x: xy[0] - W / 2,
        y: -(xy[1] - H / 2),
        value: v,
        county: info?.county_name ?? '',
        state: info?.state_name ?? '',
      });
    }

    const allValues = columns.map((c) => c.value).sort(d3.ascending);
    const lo = d3.quantile(allValues, 0.05);
    const hi = d3.quantile(allValues, 0.95);
    const colorScale = d3.scaleSequential([lo, hi], d3.interpolateRdBu);

    function rgbaFor(v) {
      const c = d3.color(colorScale(v));
      return c ? [c.r, c.g, c.b, 235] : [128, 128, 128, 235];
    }

    // State borders, projected and re-centered so they sit flat under the columns.
    const statePaths = [];
    for (const f of states.features) {
      const geometries = f.geometry?.type === 'Polygon'
        ? [f.geometry.coordinates]
        : f.geometry?.type === 'MultiPolygon'
          ? f.geometry.coordinates
          : [];
      for (const polygon of geometries) {
        for (const ring of polygon) {
          const path = ring
            .map((coord) => projection(coord))
            .filter((xy) => xy && Number.isFinite(xy[0]))
            .map(([x, y]) => [x - W / 2, -(y - H / 2), 0]);
          if (path.length > 1) statePaths.push({ path });
        }
      }
    }

    const elevationScale = 800;

    const ambient = new AmbientLight({ color: [255, 255, 255], intensity: 0.85 });
    const directional = new DirectionalLight({
      color: [255, 255, 255],
      intensity: 1.5,
      direction: [-2, -3, -1],
    });
    const lighting = new LightingEffect({ ambient, directional });

    deckInstance = new Deck({
      canvas: canvasEl,
      width: W,
      height: H,
      views: [new OrbitView({ orthographic: false })],
      initialViewState: {
        target: [0, 0, 50],
        zoom: -1.2,
        rotationX: 52,
        rotationOrbit: 0,
        minZoom: -3,
        maxZoom: 2,
      },
      controller: { dragRotate: true, scrollZoom: true, doubleClickZoom: false },
      effects: [lighting],
      layers: [
        new PathLayer({
          id: 'state-borders',
          data: statePaths,
          coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
          getPath: (d) => d.path,
          getColor: [120, 120, 130, 180],
          getWidth: 1.2,
          widthUnits: 'pixels',
        }),
        new ColumnLayer({
          id: 'mobility-3d',
          data: columns,
          coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
          diskResolution: 6,
          radius: 5,
          extruded: true,
          pickable: true,
          getPosition: (d) => [d.x, d.y, 0],
          getElevation: (d) => Math.max(2, (d.value - lo) * elevationScale),
          getFillColor: (d) => rgbaFor(d.value),
          material: { ambient: 0.55, diffuse: 0.7, shininess: 28 },
        }),
      ],
      onHover: (info) => {
        if (info.object && info.layer?.id === 'mobility-3d') {
          hover = {
            visible: true,
            x: info.x + 14,
            y: info.y + 14,
            county: info.object.county || 'Unknown',
            state: info.object.state || '',
            value: info.object.value,
          };
        } else {
          hover = { ...hover, visible: false };
        }
      },
    });

    isLoading = false;

    resizeObserver = new ResizeObserver(() => {
      if (!deckInstance || !containerEl) return;
      const newW = containerEl.clientWidth || W;
      const newH = Math.max(500, Math.round(newW * 0.62));
      deckInstance.setProps({ width: newW, height: newH });
    });
    resizeObserver.observe(containerEl);
  }

  onMount(() => {
    init().catch((err) => {
      console.error('3D init failed', err);
      errorMsg = err?.message ?? 'Failed to initialize 3D view';
      isLoading = false;
    });
  });

  onDestroy(() => {
    if (deckInstance) {
      try { deckInstance.finalize(); } catch (_) { /* ignore */ }
    }
    if (resizeObserver) resizeObserver.disconnect();
  });
</script>

<div bind:this={containerEl} class="three-d-wrapper">
  <h3>3D Mobility Map · Bonus View</h3>
  <p class="subtitle">
    Each column = one U.S. county. Height = upward mobility for children of poor parents (1992 cohort).
    Taller, bluer columns = more mobile counties.
  </p>

  <div class="canvas-wrap">
    <canvas bind:this={canvasEl} class="deck-canvas"></canvas>

    {#if isLoading}
      <div class="overlay">Loading 3D scene…</div>
    {/if}
    {#if errorMsg}
      <div class="overlay error">3D unavailable — {errorMsg}</div>
    {/if}

    {#if hover.visible}
      <div class="tooltip" style="left:{hover.x}px;top:{hover.y}px">
        <div><strong>{hover.county}{hover.state ? `, ${hover.state}` : ''}</strong></div>
        <div>Mobility: <strong>{(hover.value * 100).toFixed(1)}th</strong> percentile</div>
      </div>
    {/if}
  </div>

  <div class="footer">
    <span class="hint">Drag to orbit · Scroll to zoom · Hover a column for county detail</span>
    <span class="source">Source: Opportunity Atlas (Chetty et al.) · 1992 birth cohort</span>
  </div>
</div>

<style>
  .three-d-wrapper {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, #fafbfd 0%, #e9edf2 100%);
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.07);
    padding: 16px;
    box-sizing: border-box;
  }
  h3 { margin: 0; font-size: 1.15rem; color: #2c3e50; }
  .subtitle { margin: 4px 0 10px; font-size: 0.84rem; color: #7b8a8b; line-height: 1.5; }

  .canvas-wrap {
    position: relative;
    flex-grow: 1;
    min-height: 460px;
    overflow: hidden;
    border-radius: 8px;
    background: radial-gradient(circle at 50% 35%, #ffffff 0%, #dfe5ed 75%);
  }
  .deck-canvas {
    width: 100%;
    height: 100%;
    cursor: grab;
    display: block;
  }
  .deck-canvas:active { cursor: grabbing; }

  .overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #7f8c8d;
    font-style: italic;
    pointer-events: none;
  }
  .overlay.error { color: #c0392b; }

  .tooltip {
    position: absolute;
    background: rgba(15, 15, 20, 0.92);
    color: #fff;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 12px;
    line-height: 1.55;
    pointer-events: none;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    z-index: 10;
  }

  .footer {
    border-top: 1px solid #e3e8ee;
    margin-top: 8px;
    padding-top: 8px;
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 0.75rem;
    color: #8a92a0;
  }
  .hint { font-style: italic; }
  .source { color: #aab1bb; }
</style>

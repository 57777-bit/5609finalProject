<script>
  import { onMount, onDestroy } from 'svelte';
  import { base } from '$app/paths';
  import * as d3 from 'd3';
  import * as topojson from 'topojson-client';

  let canvasEl      = $state(null);
  let containerEl   = $state(null);
  let isLoading     = $state(true);
  let errorMsg      = $state(null);
  let hover         = $state({ visible: false, x: 0, y: 0, county: '', state: '', value: 0 });
  let focusedState  = $state(null);   // null = full U.S. view
  let geoState      = $state(null);   // auto-detected state from geolocation
  let stateStats    = $state(new Map());
  let nationalMedian = $state(0);

  let deckInstance    = null;
  let resizeObserver  = null;
  // Module-level mirror so layer callbacks (closures created at init time) see current value.
  let _focused = null;

  // ── Helpers ──────────────────────────────────────────────────────────────────

  function fireColor(t) {
    // Low → near-black | Mid → deep red | High → bright orange-red
    // On a dark background these columns glow like embers.
    if (t <= 0) return [8, 2, 2];
    if (t >= 1) return [255, 100, 20];
    const stops = [
      [0.00, [8,   2,   2 ]],
      [0.35, [80,  8,   0 ]],
      [0.60, [190, 25,  0 ]],
      [0.80, [255, 55,  5 ]],
      [1.00, [255, 100, 20]],
    ];
    let i = 0;
    while (i < stops.length - 2 && t > stops[i + 1][0]) i++;
    const [t0, c0] = stops[i];
    const [t1, c1] = stops[i + 1];
    const f = (t - t0) / (t1 - t0);
    return c0.map((v, j) => Math.round(v + (c1[j] - v) * f));
  }

  async function init() {
    // Capture DOM refs immediately before any await — HMR can null them mid-flight.
    const container = containerEl;
    const canvas    = canvasEl;
    if (!container || !canvas) return;

    const [coreModule, layersModule] = await Promise.all([
      import('@deck.gl/core'),
      import('@deck.gl/layers'),
    ]);
    const {
      Deck, OrbitView, COORDINATE_SYSTEM,
      LightingEffect, AmbientLight, DirectionalLight, LinearInterpolator,
    } = coreModule;
    const { ColumnLayer, PathLayer } = layersModule;

    const [rawData, us] = await Promise.all([
      fetch(`${base}/data/data.json`).then(r => r.json()),
      fetch(`${base}/data/counties-10m.json`).then(r => r.json()),
    ]);

    const W = container.clientWidth || 800;
    const H = Math.max(500, Math.round(W * 0.62));

    const countiesGeo = topojson.feature(us, us.objects.counties);
    const statesGeo   = topojson.feature(us, us.objects.states);
    const projection  = d3.geoAlbersUsa().fitSize([W, H], countiesGeo);

    // ── Build county columns ──────────────────────────────────────────────────
    const valueByFips = new Map();
    for (const d of rawData) {
      const v = +d.kfr_pooled_pooled_p1_1992;
      if (Number.isFinite(v)) valueByFips.set(d.fips, v);
    }

    // State FIPS (2-digit) → state name, built from county rows
    const stateFipsToName = new Map();
    for (const d of rawData) {
      if (!d.state_name) continue;
      const sf = String(d.fips).padStart(5, '0').slice(0, 2);
      stateFipsToName.set(sf, d.state_name);
    }

    const columns = [];
    for (const f of countiesGeo.features) {
      const fips = String(f.id).padStart(5, '0');
      const v = valueByFips.get(f.id) ?? valueByFips.get(fips);
      if (v == null) continue;
      const centroid = d3.geoCentroid(f);
      const xy = projection(centroid);
      if (!xy || !Number.isFinite(xy[0])) continue;
      const info = rawData.find(r => r.fips === f.id || String(r.fips).padStart(5, '0') === fips);
      columns.push({
        x: xy[0] - W / 2,
        y: -(xy[1] - H / 2),
        value: v,
        county: info?.county_name ?? '',
        state:  info?.state_name  ?? '',
        stateFips: fips.slice(0, 2),
      });
    }

    const allValues = columns.map(c => c.value).sort(d3.ascending);
    const lo = d3.quantile(allValues, 0.05);
    const hi = d3.quantile(allValues, 0.95);
    const range = hi - lo;

    function rgbaFor(v, active = true) {
      const t = Math.max(0, Math.min(1, (v - lo) / range));
      const [r, g, b] = fireColor(t);
      return [r, g, b, active ? 245 : 35];
    }

    // ── Per-state statistics ──────────────────────────────────────────────────
    const groups = new Map();
    for (const col of columns) {
      if (!col.state) continue;
      if (!groups.has(col.state)) groups.set(col.state, { cols: [], xs: [], ys: [] });
      const g = groups.get(col.state);
      g.cols.push(col); g.xs.push(col.x); g.ys.push(col.y);
    }
    const natMed = d3.median(columns, c => c.value);
    nationalMedian = natMed;

    const ranked = [...groups.entries()]
      .map(([name, g]) => {
        const vals = g.cols.map(c => c.value);
        return { name, median: d3.median(vals), mean: d3.mean(vals) };
      })
      .sort((a, b) => b.median - a.median);

    const finalStats = new Map();
    ranked.forEach(({ name, median, mean }, i) => {
      const g = groups.get(name);
      finalStats.set(name, {
        median, mean,
        rank: i + 1,
        cx: (d3.min(g.xs) + d3.max(g.xs)) / 2,
        cy: (d3.min(g.ys) + d3.max(g.ys)) / 2,
        spanX: d3.max(g.xs) - d3.min(g.xs),
        spanY: d3.max(g.ys) - d3.min(g.ys),
      });
    });
    stateStats = finalStats;

    // ── State border paths (with state name for selective highlighting) ───────
    const statePaths = [];
    for (const f of statesGeo.features) {
      const sf = String(f.id).padStart(2, '0');
      const name = stateFipsToName.get(sf) ?? '';
      const geoms = f.geometry?.type === 'Polygon'
        ? [f.geometry.coordinates]
        : f.geometry?.type === 'MultiPolygon' ? f.geometry.coordinates : [];
      for (const poly of geoms) {
        for (const ring of poly) {
          const path = ring
            .map(c => projection(c))
            .filter(xy => xy && Number.isFinite(xy[0]))
            .map(([x, y]) => [x - W / 2, -(y - H / 2), 0]);
          if (path.length > 1) statePaths.push({ path, name });
        }
      }
    }

    // ── Lighting (tuned for dark background) ─────────────────────────────────
    const lighting = new LightingEffect({
      ambient: new AmbientLight({ color: [255, 200, 180], intensity: 0.5 }),
      dir1: new DirectionalLight({ color: [255, 160, 100], intensity: 2.0, direction: [-1, -2, -1] }),
      dir2: new DirectionalLight({ color: [120,  80,  60], intensity: 0.8, direction: [ 3,  1, -1] }),
    });

    // ── Layer factory ─────────────────────────────────────────────────────────
    function buildLayers() {
      const f = _focused;
      return [
        new PathLayer({
          id: 'state-borders',
          data: statePaths,
          coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
          getPath: d => d.path,
          getColor: d => f == null
            ? [180, 180, 200, 80]
            : d.name === f
              ? [255, 100, 40, 255]   // terracotta highlight on focused state
              : [60, 60, 70, 40],
          getWidth: d => (f != null && d.name === f) ? 2.5 : 1,
          widthUnits: 'pixels',
          updateTriggers: { getColor: f, getWidth: f },
        }),
        new ColumnLayer({
          id: 'mobility-3d',
          data: columns,
          coordinateSystem: COORDINATE_SYSTEM.CARTESIAN,
          diskResolution: 8,
          radius: 5,
          extruded: true,
          pickable: true,
          getPosition: d => [d.x, d.y, 0],
          getElevation: d => Math.max(2, (d.value - lo) * 900),
          getFillColor: d => rgbaFor(d.value, f == null || d.state === f),
          material: { ambient: 0.4, diffuse: 0.8, shininess: 40, specularColor: [255, 180, 100] },
          updateTriggers: { getFillColor: f },
        }),
      ];
    }

    // ── Deck instance ─────────────────────────────────────────────────────────
    deckInstance = new Deck({
      canvas: canvas,
      width: W, height: H,
      views: [new OrbitView({ orthographic: false })],
      initialViewState: {
        target: [0, 0, 50],
        zoom: -1.2,
        rotationX: 52,
        rotationOrbit: 0,
        minZoom: -3,
        maxZoom: 3,
      },
      controller: { dragRotate: true, scrollZoom: true, doubleClickZoom: false },
      effects: [lighting],
      layers: buildLayers(),
      onHover: info => {
        if (info.object && info.layer?.id === 'mobility-3d') {
          hover = {
            visible: true,
            x: info.x + 14, y: info.y + 14,
            county: info.object.county || 'Unknown',
            state: info.object.state || '',
            value: info.object.value,
          };
        } else {
          hover = { ...hover, visible: false };
        }
      },
      onClick: info => {
        if (info.object?.state) {
          const s = info.object.state;
          if (_focused === s) { resetView(); } else { focusState(s); }
        } else if (!info.object) {
          resetView();
        }
      },
    });

    // ── Focus / reset helpers ─────────────────────────────────────────────────
    function focusState(name) {
      _focused = name;
      focusedState = name;
      const s = finalStats.get(name);
      if (!s) return;

      // Zoom to fit the state from a dramatic side angle
      const span = Math.max(s.spanX, s.spanY, 60);
      const zoomFit = Math.log2(Math.min(W, H) / span) - 0.1;
      deckInstance.setProps({
        initialViewState: {
          target: [s.cx, s.cy, 200],
          zoom: Math.min(2.0, Math.max(0.2, zoomFit)),
          rotationX: 72,           // steep side view to reveal height differences
          rotationOrbit: 18,
          transitionDuration: 1100,
          transitionInterpolator: new LinearInterpolator([
            'target', 'zoom', 'rotationX', 'rotationOrbit',
          ]),
        },
        layers: buildLayers(),
      });
    }

    function resetView() {
      _focused = null;
      focusedState = null;
      deckInstance.setProps({
        initialViewState: {
          target: [0, 0, 50],
          zoom: -1.2,
          rotationX: 52,
          rotationOrbit: 0,
          transitionDuration: 900,
          transitionInterpolator: new LinearInterpolator([
            'target', 'zoom', 'rotationX', 'rotationOrbit',
          ]),
        },
        layers: buildLayers(),
      });
    }

    // Expose to template buttons
    window.__3d_focusState = focusState;
    window.__3d_resetView  = resetView;

    isLoading = false;

    // ── Geolocation (optional, non-blocking) ─────────────────────────────────
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(pos => {
        const { latitude, longitude } = pos.coords;
        const pt = projection([longitude, latitude]);
        if (!pt) return;
        const [px, py] = [pt[0] - W / 2, -(pt[1] - H / 2)];
        let best = null, bestD = Infinity;
        for (const [name, data] of finalStats) {
          const d2 = (data.cx - px) ** 2 + (data.cy - py) ** 2;
          if (d2 < bestD) { bestD = d2; best = name; }
        }
        if (best) {
          geoState = best;
          // Auto-focus after a short pause so the user first sees the full U.S.
          setTimeout(() => focusState(best), 2800);
        }
      }, () => {/* permission denied — silent */}, { timeout: 6000 });
    }

    resizeObserver = new ResizeObserver(() => {
      if (!deckInstance) return;
      const nW = container.clientWidth || W;
      const nH = Math.max(500, Math.round(nW * 0.62));
      deckInstance.setProps({ width: nW, height: nH });
    });
    resizeObserver.observe(container);
  }

  onMount(() => {
    init().catch(err => {
      console.error('3D init failed', err);
      errorMsg = err?.message ?? 'Failed to initialize 3D view';
      isLoading = false;
    });
  });

  onDestroy(() => {
    try { deckInstance?.finalize(); } catch (_) {}
    resizeObserver?.disconnect();
    delete window.__3d_focusState;
    delete window.__3d_resetView;
  });

  // Template helpers (read Svelte state, not module vars)
  function handleReset()       { window.__3d_resetView?.(); }
  function handleFocus(name)   { window.__3d_focusState?.(name); }

  function fmtPct(v) { return (v * 100).toFixed(1); }
  function fmtDelta(v) {
    const d = (v - nationalMedian) * 100;
    return (d >= 0 ? '+' : '') + d.toFixed(1);
  }
</script>

<div bind:this={containerEl} class="three-d-wrapper">

  <div class="header-row">
    <div>
      <h3>3D Mobility Map</h3>
      <p class="subtitle">
        Each column = one U.S. county. <strong>Height & color = upward mobility</strong>
        for children of poor parents (1992 cohort). Tallest, reddest = most opportunity.
        {#if geoState && !focusedState}
          <span class="geo-hint">Detected your state: <em>{geoState}</em> — zooming in…</span>
        {/if}
      </p>
    </div>
    {#if focusedState}
      <button class="reset-btn" onclick={handleReset}>← All U.S.</button>
    {/if}
  </div>

  <div class="canvas-wrap">
    <canvas bind:this={canvasEl} class="deck-canvas"></canvas>

    {#if isLoading}
      <div class="overlay">Loading 3D scene…</div>
    {/if}
    {#if errorMsg}
      <div class="overlay error">3D unavailable — {errorMsg}</div>
    {/if}

    <!-- Hover tooltip -->
    {#if hover.visible}
      <div class="tooltip" style="left:{hover.x}px;top:{hover.y}px">
        <strong>{hover.county}{hover.state ? `, ${hover.state}` : ''}</strong><br>
        Mobility: <strong>{fmtPct(hover.value)}th percentile</strong>
        {#if nationalMedian}
          <span class:above={hover.value > nationalMedian}
                class:below={hover.value < nationalMedian}>
            ({fmtDelta(hover.value)} vs. U.S.)
          </span>
        {/if}
      </div>
    {/if}

    <!-- State comparison panel -->
    {#if focusedState && stateStats.has(focusedState)}
      {@const s = stateStats.get(focusedState)}
      <div class="compare-panel">
        <div class="compare-state">{focusedState}</div>
        <div class="compare-rank">#{s.rank} <span class="of-50">of 50 states</span></div>
        <div class="compare-stat">
          <span class="lbl">Median mobility</span>
          <span class="val">{fmtPct(s.median)}th pct.</span>
        </div>
        <div class="compare-delta"
             class:positive={(s.median - nationalMedian) >= 0}
             class:negative={(s.median - nationalMedian) < 0}>
          {fmtDelta(s.median)} pts vs. national median
        </div>
        <div class="compare-hint">Click any county · click again to reset</div>
      </div>
    {/if}
  </div>

  <div class="footer">
    <span class="hint">
      {#if focusedState}
        Side-angle view — drag to orbit · scroll to zoom · click empty area to reset
      {:else}
        Drag to orbit · scroll to zoom · <strong>click any county</strong> to zoom into that state
      {/if}
    </span>
    <span class="source">Source: Opportunity Atlas (Chetty et al.) · 1992 birth cohort</span>
  </div>
</div>

<style>
  .three-d-wrapper {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #0A0A0A;
    border-radius: 12px;
    padding: 14px 16px 10px;
    box-sizing: border-box;
    color: #E8DDD0;
  }

  .header-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
  }

  h3 {
    margin: 0 0 2px;
    font-size: 1.05rem;
    font-weight: 700;
    color: #F4EFE6;
    letter-spacing: 0.02em;
  }

  .subtitle {
    margin: 0;
    font-size: 0.8rem;
    color: #8A8278;
    line-height: 1.5;
  }
  .geo-hint {
    display: block;
    margin-top: 3px;
    color: #C07050;
    font-style: italic;
  }

  .reset-btn {
    flex-shrink: 0;
    background: none;
    border: 1px solid #B5533C;
    color: #D67A5C;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 5px 12px;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s, color 0.15s;
  }
  .reset-btn:hover { background: #B5533C; color: #F4EFE6; }

  .canvas-wrap {
    position: relative;
    flex-grow: 1;
    min-height: 460px;
    overflow: hidden;
    border-radius: 8px;
    background: #0A0A0A;
  }

  .deck-canvas { width: 100%; height: 100%; cursor: grab; display: block; }
  .deck-canvas:active { cursor: grabbing; }

  .overlay {
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
    color: #6A6260; font-style: italic; pointer-events: none;
  }
  .overlay.error { color: #c0392b; }

  .tooltip {
    position: absolute;
    background: rgba(10, 6, 4, 0.92);
    color: #F4EFE6;
    border: 1px solid #3A2010;
    padding: 7px 11px;
    border-radius: 5px;
    font-size: 0.8rem;
    line-height: 1.6;
    pointer-events: none;
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
    z-index: 10;
    max-width: 220px;
  }
  .tooltip .above { color: #FF7040; }
  .tooltip .below { color: #8AB0C0; }

  /* State comparison panel */
  .compare-panel {
    position: absolute;
    top: 14px; right: 14px;
    background: rgba(10, 6, 4, 0.88);
    border: 1px solid #3A2010;
    border-radius: 8px;
    padding: 14px 16px;
    min-width: 180px;
    backdrop-filter: blur(4px);
    pointer-events: none;
  }
  .compare-state {
    font-size: 1.0rem;
    font-weight: 700;
    color: #F4EFE6;
    margin-bottom: 4px;
  }
  .compare-rank {
    font-size: 1.6rem;
    font-weight: 800;
    color: #FF6030;
    line-height: 1;
    margin-bottom: 10px;
  }
  .of-50 { font-size: 0.75rem; font-weight: 400; color: #7A6A60; }
  .compare-stat {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    font-size: 0.78rem;
    margin-bottom: 6px;
  }
  .lbl { color: #8A8278; }
  .val { color: #F4EFE6; font-weight: 600; }
  .compare-delta {
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 10px;
  }
  .compare-delta.positive { color: #FF7040; }
  .compare-delta.negative { color: #7AABB0; }
  .compare-hint {
    font-size: 0.68rem;
    color: #5A5250;
    font-style: italic;
  }

  .footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 7px;
    gap: 8px;
    font-size: 0.72rem;
    color: #5A5250;
  }
  .hint { font-style: italic; }
  .source { color: #4A4240; text-align: right; }
</style>

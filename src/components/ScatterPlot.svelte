<!-- <script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';

  let svgEl = $state(null);
  let tooltip = $state({ visible: false, x: 0, y: 0, name: '', state: '', p1: '', p100: '' });
  let isLoading = $state(true);

  let data = $state(null);
  let geoData = null;

  onMount(async () => {
    const rawData = await fetch('/data.json').then(r => r.json());
    data = rawData;       
    isLoading = false;
  });

  $effect(() => {
    if (data && svgEl) {
      drawChart(data);
    }
  });

  function drawChart(rawData) {
    const data = rawData.filter(d =>
      d.kfr_pooled_pooled_p1_1978 != null &&
      d.kfr_pooled_pooled_p100_1978 != null
    );

    const margin = { top: 40, right: 40, bottom: 60, left: 70 };
    const width = svgEl.clientWidth || 800;
    const height = 500;
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    const svg = d3.select(svgEl)
      .attr('viewBox', `0 0 ${width} ${height}`);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear()
      .domain(d3.extent(data, d => d.kfr_pooled_pooled_p1_1978)).nice()
      .range([0, innerW]);

    // const y = d3.scaleLinear()
    //   .domain(d3.extent(data, d => d.kfr_pooled_pooled_p100_1978)).nice()
    //   .range([innerH, 0]);
    const yValues = data.map(d => d.kfr_pooled_pooled_p100_1978).sort(d3.ascending);

  const yMin = d3.quantile(yValues, 0.01);
  const yMax = d3.quantile(yValues, 0.99);

  const filteredData = data.filter(d =>
    d.kfr_pooled_pooled_p100_1978 >= yMin &&
    d.kfr_pooled_pooled_p100_1978 <= yMax
  );

  const y = d3.scaleLinear()
    .domain([yMin, yMax])
    .nice()
    .range([innerH, 0]);

    const slopeExtent = d3.extent(data, d =>
      d.kfr_pooled_pooled_p100_1978 - d.kfr_pooled_pooled_p1_1978
    );
    const colorScale = d3.scaleSequential()
      .domain(slopeExtent)
      .interpolator(d3.interpolateRdYlGn)
      ;
    const colorScaleReversed = d3.scaleSequential()
      .domain([slopeExtent[1], slopeExtent[0]])
      .interpolator(d3.interpolateRdYlGn);

    // 网格线
    g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6).tickSize(-innerH).tickFormat(''))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('line').attr('stroke', '#eee'));

    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(y).ticks(6).tickSize(-innerW).tickFormat(''))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('line').attr('stroke', '#eee'));

    const diagMin = Math.max(x.domain()[0], y.domain()[0]);
    const diagMax = Math.min(x.domain()[1], y.domain()[1]);
    g.append('line')
      .attr('x1', x(diagMin)).attr('y1', y(diagMin))
      .attr('x2', x(diagMax)).attr('y2', y(diagMax))
      .attr('stroke', '#aaa')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4 3');

    g.append('text')
      .attr('x', x(diagMax) - 10)
      .attr('y', y(diagMax) - 8)
      .style('font-size', '11px')
      .style('fill', '#999')
      .text('Line of perfect equality');

    g.selectAll('circle')
      .data(data)
      .join('circle')
      .attr('cx', d => x(d.kfr_pooled_pooled_p1_1978))
      .attr('cy', d => y(d.kfr_pooled_pooled_p100_1978))
      .attr('r', 3)
      .attr('fill', d => colorScaleReversed(
        d.kfr_pooled_pooled_p100_1978 - d.kfr_pooled_pooled_p1_1978
      ))
      .attr('opacity', 0.7)
      .on('mouseover', function(event, d) {
        d3.select(this).attr('r', 6).attr('opacity', 1);
        tooltip = {
          visible: true,
          x: event.offsetX + 12,
          y: event.offsetY - 28,
          name: d.county_name ?? 'unknown county',
          state: d.state_name ?? '',
          p1: (d.kfr_pooled_pooled_p1_1978 * 100).toFixed(1),
          p100: (d.kfr_pooled_pooled_p100_1978 * 100).toFixed(1),
          gap: ((d.kfr_pooled_pooled_p100_1978 - d.kfr_pooled_pooled_p1_1978) * 100).toFixed(1)
        };
      })
      .on('mousemove', function(event) {
        tooltip = { ...tooltip, x: event.offsetX + 12, y: event.offsetY - 28 };
      })
      .on('mouseout', function() {
        d3.select(this).attr('r', 3).attr('opacity', 0.7);
        tooltip = { ...tooltip, visible: false };
      });

    g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat(d => `${(d*100).toFixed(0)}th`))
      .call(g => g.select('.domain').attr('stroke', '#ccc'))
      .call(g => g.selectAll('text').style('font-size', '11px'));

    g.append('g')
      .call(d3.axisLeft(y).ticks(6).tickFormat(d => `${(d*100).toFixed(0)}th`))
      .call(g => g.select('.domain').attr('stroke', '#ccc'))
      .call(g => g.selectAll('text').style('font-size', '11px'));

    g.append('text')
      .attr('x', innerW / 2).attr('y', innerH + 48)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px').style('fill', '#555')
      .text('Children’s income percentile (parents at P1)');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerH / 2).attr('y', -52)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px').style('fill', '#555')
      .text('Children’s income percentile (parents at P100)');
  }
</script>

<div class="chart-container">
  <h2>Mobility Slope Analysis: The Impact of Parental Income on Children's Outcomes</h2>
  <p class="desc">
    Each point represents a county. The closer a point is to the diagonal line, the weaker the influence of parental income on children (i.e., more equal opportunity).
    Greener colors indicate a smaller income gap, while redder colors indicate a larger gap.
  </p>
  {#if isLoading}
    <div class="loading">Loading...</div>
  {:else}
    <div class="wrapper">
      <svg bind:this={svgEl} style="width:100%; display:block;"></svg>
      {#if tooltip.visible}
        <div class="tooltip" style="left:{tooltip.x}px; top:{tooltip.y}px">
          <strong>{tooltip.name}, {tooltip.state}</strong><br/>
          Children's income percentile (parents at P1): {tooltip.p1}th<br/>
          Children's income percentile (parents at P100): {tooltip.p100}th<br/>
          Gap: <strong>{tooltip.gap}</strong> percentile points
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .chart-container { width: 100%; font-family: sans-serif; margin-top: 1rem; }
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

  let svgEl = $state(null);
  let tooltip = $state({
    visible: false,
    x: 0,
    y: 0,
    name: '',
    state: '',
    p1: '',
    p100: '',
    gap: ''
  });
  let isLoading = $state(true);
  let data = $state(null);

  onMount(async () => {
    const rawData = await fetch(`${base}/data/data.json`).then(r => r.json());
    data = rawData;
    isLoading = false;
  });

  $effect(() => {
    if (data && svgEl) {
      drawChart(data);
    }
  });

  function drawChart(rawData) {
  //   const validData = rawData.filter(d =>
  //     d.kfr_pooled_pooled_p1_1978 != null &&
  //     d.kfr_pooled_pooled_p100_1978 != null
  //   );
  const validData = rawData.filter(d =>
    d.kfr_pooled_pooled_p1_1978 != null &&
    d.kfr_pooled_pooled_p100_1978 != null
  );

  const filteredData = validData.filter(d =>
    d.kfr_pooled_pooled_p1_1978 >= 0 &&
    d.kfr_pooled_pooled_p1_1978 <= 1 &&
    d.kfr_pooled_pooled_p100_1978 >= 0 &&
    d.kfr_pooled_pooled_p100_1978 <= 1
  );

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();

    const margin = { top: 50, right: 30, bottom: 70, left: 75 };
    const width = svgEl.clientWidth || 850;
    const height = 560;
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // 1) sampling: keep about 600 points to avoid overplotting
    // const targetPoints = 600;
    // const step = Math.max(1, Math.ceil(validData.length / targetPoints));
    // const sampledData = validData.filter((_, i) => i % step === 0);
    const targetPoints = 600;
    const step = Math.max(1, Math.ceil(filteredData.length / targetPoints));
    const sampledData = filteredData.filter((_, i) => i % step === 0);

    // axis domains with small padding
    const xExtent = d3.extent(sampledData, d => d.kfr_pooled_pooled_p1_1978);
    const yExtent = d3.extent(sampledData, d => d.kfr_pooled_pooled_p100_1978);

    const xPad = 0.02;
    const yPad = 0.02;

    const x = d3.scaleLinear()
      .domain([xExtent[0] - xPad, xExtent[1] + xPad])
      .nice()
      .range([0, innerW]);

    const y = d3.scaleLinear()
      .domain([yExtent[0] - yPad, yExtent[1] + yPad])
      .nice()
      .range([innerH, 0]);

    // 2) consistent color meaning:
    // teal = smaller gap = more equal
    // yellow = medium gap
    // red = larger gap = more unequal
    const gapExtent = d3.extent(
      sampledData,
      d => d.kfr_pooled_pooled_p100_1978 - d.kfr_pooled_pooled_p1_1978
    );

    const gapMid = (gapExtent[0] + gapExtent[1]) / 2;

    const gapColor = d3.scaleLinear()
      .domain([gapExtent[0], gapMid, gapExtent[1]])
      .range(['#2A9D8F', '#E9C46A', '#E63946']);

    // gridlines
    g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6).tickSize(-innerH).tickFormat(''))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('line').attr('stroke', '#e9e9e9'));

    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(y).ticks(6).tickSize(-innerW).tickFormat(''))
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('line').attr('stroke', '#e9e9e9'));

    // diagonal equality line
    const diagMin = Math.max(x.domain()[0], y.domain()[0]);
    const diagMax = Math.min(x.domain()[1], y.domain()[1]);

    g.append('line')
      .attr('x1', x(diagMin))
      .attr('y1', y(diagMin))
      .attr('x2', x(diagMax))
      .attr('y2', y(diagMax))
      .attr('stroke', '#999')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '6 4');

    g.append('text')
      .attr('x', x(diagMax) - 8)
      .attr('y', y(diagMax) - 10)
      .attr('text-anchor', 'end')
      .style('font-size', '11px')
      .style('fill', '#777')
      .text('Equal outcomes line');

    // axes
    g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat(d => `${(d * 100).toFixed(0)}th`))
      .call(g => g.select('.domain').attr('stroke', '#bbb'))
      .call(g => g.selectAll('text').style('font-size', '11px'));

    g.append('g')
      .call(d3.axisLeft(y).ticks(6).tickFormat(d => `${(d * 100).toFixed(0)}th`))
      .call(g => g.select('.domain').attr('stroke', '#bbb'))
      .call(g => g.selectAll('text').style('font-size', '11px'));

    // axis labels
    g.append('text')
      .attr('x', innerW / 2)
      .attr('y', innerH + 50)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#555')
      .text("Children's income percentile (parents at P1)");

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerH / 2)
      .attr('y', -55)
      .attr('text-anchor', 'middle')
      .style('font-size', '12px')
      .style('fill', '#555')
      .text("Children's income percentile (parents at P100)");

    // points
    const dots = g.selectAll('circle')
      .data(sampledData)
      .join('circle')
      .attr('cx', d => x(d.kfr_pooled_pooled_p1_1978))
      .attr('cy', d => y(d.kfr_pooled_pooled_p100_1978))
      .attr('r', 4.5)
      .attr('fill', d =>
        gapColor(d.kfr_pooled_pooled_p100_1978 - d.kfr_pooled_pooled_p1_1978)
      )
      .attr('opacity', 0.72)
      .attr('stroke', '#fff')
      .attr('stroke-width', 0.6);

    // 3) hover dimming
    dots
      .on('mouseover', function (event, d) {
        dots.transition().duration(150).attr('opacity', 0.08);

        d3.select(this)
          .raise()
          .transition()
          .duration(150)
          .attr('r', 8)
          .attr('opacity', 1)
          .attr('stroke', '#333')
          .attr('stroke-width', 1.5);

        tooltip = {
          visible: true,
          x: event.offsetX + 12,
          y: event.offsetY - 28,
          name: d.county_name ?? 'unknown county',
          state: d.state_name ?? '',
          p1: (d.kfr_pooled_pooled_p1_1978 * 100).toFixed(1),
          p100: (d.kfr_pooled_pooled_p100_1978 * 100).toFixed(1),
          gap: ((d.kfr_pooled_pooled_p100_1978 - d.kfr_pooled_pooled_p1_1978) * 100).toFixed(1)
        };
      })
      .on('mousemove', function (event) {
        tooltip = {
          ...tooltip,
          x: event.offsetX + 12,
          y: event.offsetY - 28
        };
      })
      .on('mouseout', function () {
        dots.transition().duration(180)
          .attr('r', 4.5)
          .attr('opacity', 0.72)
          .attr('stroke', '#fff')
          .attr('stroke-width', 0.6);

        tooltip = { ...tooltip, visible: false };
      });

    // 4) annotation
    g.append('text')
      .attr('x', innerW / 2)
      .attr('y', 18)
      .attr('text-anchor', 'middle')
      .style('font-size', '13px')
      .style('font-weight', '600')
      .style('fill', '#666')
      .text('Almost all counties lie above the diagonal — rich kids do better almost everywhere');

    // 5) legend
    const legendWidth = 220;
    const legendHeight = 10;
    const legendX = innerW - legendWidth - 10;
    const legendY = innerH - 25;

    const defs = svg.append('defs');
    const gradient = defs.append('linearGradient')
      .attr('id', 'gap-gradient')
      .attr('x1', '0%')
      .attr('x2', '100%')
      .attr('y1', '0%')
      .attr('y2', '0%');

    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#2A9D8F');

    gradient.append('stop')
      .attr('offset', '50%')
      .attr('stop-color', '#E9C46A');

    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#E63946');

    const legend = g.append('g')
      .attr('transform', `translate(${legendX},${legendY})`);

    legend.append('rect')
      .attr('width', legendWidth)
      .attr('height', legendHeight)
      .attr('rx', 3)
      .attr('fill', 'url(#gap-gradient)');

    legend.append('text')
      .attr('x', 0)
      .attr('y', 24)
      .style('font-size', '11px')
      .style('fill', '#666')
      .text('Small gap');

    legend.append('text')
      .attr('x', legendWidth / 2)
      .attr('y', 24)
      .attr('text-anchor', 'middle')
      .style('font-size', '11px')
      .style('fill', '#666')
      .text('Income gap');

    legend.append('text')
      .attr('x', legendWidth)
      .attr('y', 24)
      .attr('text-anchor', 'end')
      .style('font-size', '11px')
      .style('fill', '#666')
      .text('Large gap');
  }
</script>

<div class="chart-container">
  <h2>Mobility Slope Analysis: The Impact of Parental Income on Children's Outcomes</h2>
  <p class="desc">
    Each point represents a county. The closer a point is to the diagonal line, the weaker the influence of parental income on children.
    Teal indicates a smaller rich-poor gap, while red indicates a larger gap.
  </p>

  {#if isLoading}
    <div class="loading">Loading...</div>
  {:else}
    <div class="wrapper">
      <svg bind:this={svgEl} style="width:100%; display:block;"></svg>

      {#if tooltip.visible}
        <div class="tooltip" style="left:{tooltip.x}px; top:{tooltip.y}px">
          <strong>{tooltip.name}, {tooltip.state}</strong><br />
          Children's income percentile (parents at P1): {tooltip.p1}th<br />
          Children's income percentile (parents at P100): {tooltip.p100}th<br />
          Gap: <strong>{tooltip.gap}</strong> percentile points
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .chart-container {
    width: 100%;
    font-family: sans-serif;
    margin-top: 1rem;
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
    margin-bottom: 0.5rem;
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
    background: rgba(0, 0, 0, 0.82);
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
    pointer-events: none;
    line-height: 1.7;
    max-width: 260px;
    white-space: normal;
  }
</style>
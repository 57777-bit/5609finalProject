<script>
    import { onMount } from 'svelte';
    import { base } from '$app/paths';
    import * as d3 from 'd3';

    let chartContainer;
    let tooltipOpacity = $state(0);
    let tooltipX = $state(0);
    let tooltipY = $state(0);
    let tooltipContent = $state({ country: '', central: 0, local: 0 });

    onMount(() => {
        d3.csv(`${base}/data/school_funding.csv`).then((data) => {
            
            const targetCountries = ["United States", "United Kingdom", "Japan", "Norway", "Sweden", "Denmark"];
            
            let filteredData = data.filter(d => targetCountries.includes(d.country));

            filteredData.forEach(d => {
                d.central = +d.central;
                d.local = +d.local;
            });

            filteredData.sort((a, b) => a.country === "United States" ? -1 : b.country === "United States" ? 1 : a.local - b.local);

            chartContainer.innerHTML = '';

            const margin = { top: 50, right: 40, bottom: 60, left: 130 };
            const width = 750 - margin.left - margin.right;
            const height = 400 - margin.top - margin.bottom;

            const svg = d3.select(chartContainer)
                .append("svg")
                .attr("width", "100%")
                .attr("height", "100%")
                .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
                .append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);

            const stack = d3.stack().keys(["central", "local"]);
            const stackedData = stack(filteredData);

            const x = d3.scaleLinear().domain([0, 100]).range([0, width]);
            svg.append("g")
                .attr("transform", `translate(0,${height})`)
                .call(d3.axisBottom(x).ticks(5).tickFormat(d => d + "%"))
                .attr("font-size", "12px").attr("color", "#7f8c8d");

            svg.append("text")
                .attr("x", width / 2)
                .attr("y", height + 45)
                .style("text-anchor", "middle")
                .style("font-weight", "bold")
                .style("font-size", "13px")
                .style("fill", "#7f8c8d")
                .text("Percentage of Total Education Funding");

            const y = d3.scaleBand()
                .domain(filteredData.map(d => d.country))
                .range([0, height])
                .padding(0.3);

            svg.append("g")
                .call(d3.axisLeft(y).tickSize(0))
                .attr("font-size", "14px").attr("font-weight", "bold")
                .style("color", "#2c3e50").select(".domain").remove();

            const color = d3.scaleOrdinal()
                .domain(["central", "local"])
                .range(["#3498db", "#e74c3c"]); 

            const handleMouseOver = (event, d, key) => {
                tooltipOpacity = 1;
                tooltipX = event.clientX + 15;
                tooltipY = event.clientY - 20;
                tooltipContent = { country: d.data.country, central: d.data.central, local: d.data.local };
                d3.select(event.currentTarget).attr("opacity", 0.8);
            };

            const handleMouseOut = (event) => {
                tooltipOpacity = 0;
                d3.select(event.currentTarget).attr("opacity", 1);
            };

            svg.append("g")
                .selectAll("g")
                .data(stackedData)
                .enter().append("g")
                .attr("fill", d => color(d.key))
                .selectAll("rect")
                .data(d => d.map(item => { item.key = d.key; return item; }))
                .enter().append("rect")
                .attr("y", d => y(d.data.country))
                .attr("x", d => x(d[0]))
                .attr("height", y.bandwidth())
                .attr("width", 0) 
                .style("cursor", "pointer")
                .on("mouseover", function(event, d) { handleMouseOver(event, d, d.key); })
                .on("mouseout", handleMouseOut)
                .on("mousemove", (event) => { tooltipX = event.clientX + 15; tooltipY = event.clientY - 20; })
                .transition() 
                .duration(800)
                .attr("width", d => x(d[1]) - x(d[0]));

            svg.append("text").attr("x", -80).attr("y", -25).attr("font-size", "20px").attr("font-weight", "bold").style("fill", "#2c3e50").text("Who Pays for Schools?");
            
            svg.append("rect").attr("x", width - 260).attr("y", -35).attr("width", 12).attr("height", 12).style("fill", "#3498db");
            svg.append("text").attr("x", width - 240).attr("y", -25).text("Central/Federal").style("font-size", "12px").attr("fill", "#7f8c8d");
            
            svg.append("rect").attr("x", width - 120).attr("y", -35).attr("width", 12).attr("height", 12).style("fill", "#e74c3c");
            svg.append("text").attr("x", width - 100).attr("y", -25).text("Local/State").style("font-size", "12px").attr("fill", "#7f8c8d");
        });
    });
</script>

<div class="chart-wrapper">
    <div bind:this={chartContainer} class="d3-container"></div>
    <div class="chart-footer">
        <div class="instructions">
            <strong>Instruction:</strong> Hover over the bar segments to see the exact funding breakdown.
        </div>
        <div class="citation">
            Source: OECD Education at a Glance (2021).
        </div>
    </div>
</div>

<div class="tooltip" style="opacity: {tooltipOpacity}; visibility: {tooltipOpacity === 0 ? 'hidden' : 'visible'}; left: {tooltipX}px; top: {tooltipY}px;">
    <strong>{tooltipContent.country}</strong><br/>
    <span style="color: #3498db;">Central Funding: {tooltipContent.central}%</span><br/>
    <span style="color: #e74c3c;">Local Funding: {tooltipContent.local}%</span>
</div>

<style>
    .chart-wrapper { width: 100%; height: 100%; display: flex; flex-direction: column; background-color: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); padding: 20px; box-sizing: border-box; }
    .d3-container { width: 100%; flex-grow: 1; }
    .chart-footer { width: 100%; display: flex; justify-content: space-between; align-items: flex-end; font-size: 0.85rem; color: #7f8c8d; border-top: 1px solid #ecf0f1; padding-top: 12px; margin-top: 10px; }
    .instructions { color: #2c3e50; }
    .citation { text-align: right; }
    .tooltip { position: fixed; background-color: rgba(255, 255, 255, 0.95); padding: 10px; border-radius: 6px; box-shadow: 0 2px 10px rgba(0,0,0,0.15); border: 1px solid #ecf0f1; pointer-events: none; font-size: 0.9rem; line-height: 1.4; transition: opacity 0.15s ease; z-index: 1000; color: #333; }
</style>
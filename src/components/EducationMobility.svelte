<script>
    import { onMount } from 'svelte';
    import * as d3 from 'd3';

    let chartContainer;
    
    // Reactive tooltip state
    let tooltipOpacity = $state(0);
    let tooltipX = $state(0);
    let tooltipY = $state(0);
    let tooltipContent = $state({ country: '', parent: 0, child: 0 });

    onMount(() => {
        d3.csv('/data/GDIM.csv').then((raw) => {
            const targetCountries = ["United States", "United Kingdom", "Japan", "Norway", "Sweden", "Denmark", "Germany", "South Africa"];
            
            let filteredData = raw.filter(d => 
                targetCountries.includes(d.country) && d.child === 'all'
            );

            const grouped = d3.group(filteredData, d => d.country);
            let data = Array.from(grouped, ([country, rows]) => {
                rows.sort((a, b) => b.cohort.localeCompare(a.cohort));
                const newestCohort = rows[0]; 
                return {
                    country: newestCohort.country,
                    parentEdu: +newestCohort.MEANp,
                    childEdu: +newestCohort.MEANc
                };
            });

            data.sort((a, b) => (b.childEdu - b.parentEdu) - (a.childEdu - a.parentEdu));

            chartContainer.innerHTML = '';

            // Increased bottom margin from 60 to 70 to make room for the new axis label
            const margin = { top: 60, right: 40, bottom: 70, left: 130 };
            const width = 750 - margin.left - margin.right;
            const height = 450 - margin.top - margin.bottom;

            const svg = d3.select(chartContainer)
                .append("svg")
                .attr("width", "100%")
                .attr("height", "100%")
                .attr("viewBox", `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
                .append("g")
                .attr("transform", `translate(${margin.left},${margin.top})`);

            const minEdu = Math.floor(d3.min(data, d => Math.min(d.parentEdu, d.childEdu))) - 1;
            const maxEdu = Math.ceil(d3.max(data, d => Math.max(d.parentEdu, d.childEdu))) + 1;

            // X axis
            const x = d3.scaleLinear().domain([minEdu, maxEdu]).range([0, width]);
            svg.append("g")
                .attr("transform", `translate(0,${height})`)
                .call(d3.axisBottom(x).ticks(6))
                .attr("color", "#7f8c8d").attr("font-size", "12px");

            // FIX: X axis label (Smaller, softer color, pushed down)
            svg.append("text")
                .attr("x", width / 2)
                .attr("y", height + 50) // Pushed further from the numbers
                .style("text-anchor", "middle")
                .style("font-weight", "bold")
                .style("font-size", "13px")
                .style("fill", "#7f8c8d")
                .text("Average Years of Schooling");

            // Y axis
            const y = d3.scaleBand().range([0, height]).domain(data.map(d => d.country)).padding(1);
            svg.append("g")
                .call(d3.axisLeft(y).tickSize(0))
                .attr("font-size", "14px").attr("font-weight", "bold")
                .style("color", "#2c3e50").select(".domain").remove();

            // FIX: Y axis label (Smaller, softer color, pushed left)
            svg.append("text")
                .attr("transform", "rotate(-90)")
                .attr("y", -margin.left + 15) // Pushed further left
                .attr("x", -(height / 2))
                .style("text-anchor", "middle")
                .style("font-weight", "bold")
                .style("font-size", "13px")
                .style("fill", "#7f8c8d")
                .text("Country");

            // FIX: Changed pageX/pageY to clientX/clientY for reliable fixed positioning
            const handleMouseOver = (event, d) => {
                tooltipOpacity = 1;
                tooltipX = event.clientX + 15;
                tooltipY = event.clientY - 20;
                tooltipContent = { country: d.country, parent: d.parentEdu, child: d.childEdu };
                d3.select(event.currentTarget).attr("stroke", "#34495e").attr("stroke-width", 6);
            };

            const handleMouseOut = (event, d) => {
                tooltipOpacity = 0;
                d3.select(event.currentTarget).attr("stroke", "#bdc3c7").attr("stroke-width", 4);
            };

            // Draw Lines
            svg.selectAll(".line")
                .data(data).enter().append("line")
                .attr("x1", d => x(d.parentEdu)).attr("x2", d => x(d.childEdu))
                .attr("y1", d => y(d.country)).attr("y2", d => y(d.country))
                .attr("stroke", "#bdc3c7").attr("stroke-width", 4)
                .style("cursor", "pointer")
                .on("mouseover", handleMouseOver).on("mouseout", handleMouseOut)
                .on("mousemove", (event) => { 
                    tooltipX = event.clientX + 15; 
                    tooltipY = event.clientY - 20; 
                });

            // Draw Dots
            svg.selectAll(".parentDot").data(data).enter().append("circle")
                .attr("cx", d => x(d.parentEdu)).attr("cy", d => y(d.country)).attr("r", 7).style("fill", "#e74c3c").style("pointer-events", "none"); 
            svg.selectAll(".childDot").data(data).enter().append("circle")
                .attr("cx", d => x(d.childEdu)).attr("cy", d => y(d.country)).attr("r", 7).style("fill", "#2ecc71").style("pointer-events", "none");
                
            // Chart Title & Legend
            svg.append("text").attr("x", -80).attr("y", -30).attr("font-size", "20px").attr("font-weight", "bold").style("fill", "#2c3e50").text("Educational Mobility Gap");
            svg.append("circle").attr("cx", width - 130).attr("cy", -35).attr("r", 5).style("fill", "#e74c3c");
            svg.append("text").attr("x", width - 120).attr("y", -31).text("Parents").style("font-size", "12px").attr("alignment-baseline","middle");
            svg.append("circle").attr("cx", width - 60).attr("cy", -35).attr("r", 5).style("fill", "#2ecc71");
            svg.append("text").attr("x", width - 50).attr("y", -31).text("Children").style("font-size", "12px").attr("alignment-baseline","middle");
        });
    });
</script>

<div class="chart-wrapper">
    <div bind:this={chartContainer} class="d3-container"></div>
    
    <div class="chart-footer">
        <div class="instructions">
            <strong>Instruction:</strong> Hover over the gray connecting lines to see the exact education gap in years.
        </div>
        <div class="citation">
            Source: Global Database on Intergenerational Mobility (GDIM), World Bank Group (2018).
        </div>
    </div>
</div>

<div 
    class="tooltip" 
    style="opacity: {tooltipOpacity}; visibility: {tooltipOpacity === 0 ? 'hidden' : 'visible'}; left: {tooltipX}px; top: {tooltipY}px;"
>
    <strong>{tooltipContent.country}</strong><br/>
    <span style="color: #e74c3c;">Parents: {(Math.round(tooltipContent.parent * 10) / 10).toFixed(1)} yrs</span><br/>
    <span style="color: #2ecc71;">Children: {(Math.round(tooltipContent.child * 10) / 10).toFixed(1)} yrs</span><br/>
    <em>Gap: +{(Math.round((tooltipContent.child - tooltipContent.parent) * 10) / 10).toFixed(1)} yrs</em>
</div>

<style>
    .chart-wrapper {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        padding: 20px;
        box-sizing: border-box;
    }
    .d3-container {
        width: 100%;
        flex-grow: 1; 
    }
    .chart-footer {
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        font-size: 0.85rem;
        color: #7f8c8d;
        border-top: 1px solid #ecf0f1;
        padding-top: 12px;
        margin-top: 10px;
    }
    .instructions {
        color: #2c3e50;
    }
    .citation {
        text-align: right;
    }
    .tooltip {
        position: fixed; /* FIX: Prevents scroll/layout offset bugs */
        background-color: rgba(255, 255, 255, 0.95);
        padding: 10px;
        border-radius: 6px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        border: 1px solid #ecf0f1;
        pointer-events: none; /* Prevents tooltip from blocking the mouse */
        font-size: 0.9rem;
        line-height: 1.4;
        transition: opacity 0.15s ease;
        z-index: 1000;
        color: #333;
    }
</style>
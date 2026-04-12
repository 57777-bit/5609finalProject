<!-- <script>
    import { onMount } from 'svelte';
    import { fade, fly } from 'svelte/transition';
    import SchoolFunding from '../components/SchoolFunding.svelte';
    import ChangeMap from '../components/ChangeMap.svelte';
    import ScatterPlot from '../components/ScatterPlot.svelte'; 
    import ScrollyMap, { STEPS as MAP_STEPS } from '../components/ScrollyMap.svelte';

    let currentStep = $state(0);
    let mapStep = $state(0);

    const steps = [
    { 
        id: 0, 
        title: "The Geographic Lottery", 
        content: "For children born into low-income families, their adult economic success is highly dependent on their specific county of birth. Why does a zip code matter so much in the U.S.?" 
    },
    { 
        id: 1, 
        title: "The Local Funding Trap", 
        content: "It matters because we don't pool our resources. Take education: unlike peer nations that fund schools centrally to ensure equality, the U.S. relies on local property taxes. If your county is poor, your public resources are poor." 
    },
    { 
        id: 2, 
        title: "The Redistribution Gap", 
        content: "This hyper-local, 'you get what you pay for' system applies to our entire economy. Before taxes and transfers, the U.S. has similar market inequality to Europe. The difference is that peer nations use government policy to redistribute wealth. We do not." 
    },
    { 
        id: 3, 
        title: "What Inequality Costs", 
        content: "This extreme concentration of wealth at the top has severe consequences. As inequality rises, life expectancy drops." 
    }
];

    onMount(() => {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    currentStep = parseInt(entry.target.dataset.step);
                }
            });
        }, { rootMargin: '-50% 0px -50% 0px' }); 

        const stepElements = document.querySelectorAll('.step');
        stepElements.forEach(el => observer.observe(el));

        return () => observer.disconnect();
    });
</script>

<div class="layout">
    <div class="story">
        <div class="header">
            <h1>The Geography of Opportunity</h1>
            <p>Scroll down to explore the data ↓</p>
        </div>

        {#each steps as step}
            <div class="step" data-step={step.id} class:active={currentStep === step.id}>
                <h2>{step.title}</h2>
                <p>{step.content}</p>
            </div>
        {/each}

        <div class="footer">
            <h2>Feedback & Discussion</h2>
            <p>What did you think of the transition from US to Global data?</p>
        </div>
    </div>

    <div class="visual-stage">
        <div class="sticky-container">
            {#if currentStep === 0}
                <!-- <div in:fade out:fade class="chart-box viz-1">Finding 1: US Maps Go Here</div> 
                <div in:fade out:fade class="chart-box">
                    <ChangeMap />
                </div>
            {:else if currentStep === 1}
                <div in:fly={{x: 200}} out:fade class="chart-box">
                    <SchoolFunding />
                </div>
            {:else if currentStep === 2}
                <!-- <div in:fade out:fade class="chart-box viz-2">Finding 2: Slopegraph Goes Here</div> 
                <div in:fade out:fade class="chart-box">
                    <ScatterPlot />
                </div>
            {:else if currentStep === 3}
                <div in:fade out:fade class="chart-box viz-3">Finding 3: Scatter Plot Goes Here</div>
            {/if}
        </div>
    </div>
</div>

<style>
    .layout {
        display: flex;
        width: 100%;
    }

    .story {
        width: 40%;
        padding: 0 2rem;
        z-index: 10;
    }

    .header, .footer {
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .step {
        height: 100vh; 
        display: flex;
        flex-direction: column;
        justify-content: center;
        opacity: 0.3; 
        transition: opacity 0.5s ease;
    }

    .step.active {
        opacity: 1; 
    }

    .step h2 {
        font-size: 2rem;
        color: #2c3e50;
    }

    .step p {
        font-size: 1.25rem;
        line-height: 1.6;
        color: #34495e;
    }

    .visual-stage {
        width: 60%;
    }

    .sticky-container {
        position: sticky;
        top: 0;
        height: 100vh;
        display: grid;
        align-items: center;
        justify-content: center;
        background-color: #ffffff;
        border-left: 1px solid #e0e0e0;
    }

    .chart-box {
        width: 95%;
        aspect-ratio: 16 / 9; 
        max-height: 85vh; 
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: bold;
        color: white;
        border-radius: 12px;
        grid-column: 1; 
        grid-row: 1;
    }

    .viz-1 { background-color: #3498db; }
    .viz-2 { background-color: #e74c3c; }
    .viz-3 { background-color: #9b59b6; }
    .viz-4 { background-color: #f1c40f; color: #333; }
    .title-stage { background-color: #2c3e50; }
</style> -->


<script>
    import { onMount } from 'svelte';
    import { fade, fly } from 'svelte/transition';
    import SchoolFunding from '../components/SchoolFunding.svelte';
    import ChangeMap from '../components/ChangeMap.svelte';
    import ScatterPlot from '../components/ScatterPlot.svelte';
    import Scrollymap, { STEPS as MAP_STEPS } from '../components/Scrollymap.svelte';

    let currentStep = $state(0);
    let mapStep = $state(0);

    const steps = [
        { 
            id: 0, 
            title: "The Geographic Lottery", 
            content: "For children born into low-income families, their adult economic success is highly dependent on their specific county of birth. Why does a zip code matter so much in the U.S.?" 
        },
        { 
            id: 1, 
            title: "The Local Funding Trap", 
            content: "It matters because we don't pool our resources. Take education: unlike peer nations that fund schools centrally to ensure equality, the U.S. relies on local property taxes. If your county is poor, your public resources are poor." 
        },
        { 
            id: 2, 
            title: "The Redistribution Gap", 
            content: "This hyper-local, 'you get what you pay for' system applies to our entire economy. Before taxes and transfers, the U.S. has similar market inequality to Europe. The difference is that peer nations use government policy to redistribute wealth. We do not." 
        },
        { 
            id: 3, 
            title: "What Inequality Costs", 
            content: "This extreme concentration of wealth at the top has severe consequences. As inequality rises, life expectancy drops." 
        }
    ];

    onMount(() => {
        // ── Outer observer: drives currentStep (which chart to show) ──
        const outerObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    currentStep = parseInt(entry.target.dataset.step);
                }
            });
        }, { rootMargin: '-50% 0px -50% 0px' });

        document.querySelectorAll('.step').forEach(el => outerObserver.observe(el));

        // ── Inner observer: drives mapStep inside Step 0's sub-steps ──
        const innerObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    mapStep = parseInt(entry.target.dataset.mapStep);
                }
            });
        }, { rootMargin: '-50% 0px -50% 0px' });

        document.querySelectorAll('.map-sub-step').forEach(el => innerObserver.observe(el));

        return () => {
            outerObserver.disconnect();
            innerObserver.disconnect();
        };
    });
</script>

<div class="layout">
    <div class="story">
        <div class="header">
            <h1>The Geography of Opportunity</h1>
            <p>Scroll down to explore the data ↓</p>
        </div>

        <!-- ── Step 0: expanded into MAP_STEPS sub-steps ── -->
        <!-- data-step=0 sits on the wrapper so outerObserver fires when ANY sub-step is visible -->
        <div class="step step-0" data-step={0} class:active={currentStep === 0}>
            {#each MAP_STEPS as mapStepDef}
                <div class="map-sub-step" data-map-step={mapStepDef.id}>
                    <h2>{mapStepDef.title}</h2>
                    <p>{mapStepDef.content}</p>
                    {#if mapStepDef.statNum}
                        <div class="stat-block" style="--stat-color: {mapStepDef.statColor}">
                            <span class="stat-num">{mapStepDef.statNum}</span>
                            <span class="stat-label">{mapStepDef.statLabel}</span>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>

        <!-- ── Steps 1–3: unchanged ── -->
        {#each steps.slice(1) as step}
            <div class="step" data-step={step.id} class:active={currentStep === step.id}>
                <h2>{step.title}</h2>
                <p>{step.content}</p>
            </div>
        {/each}

        <div class="footer">
            <h2>Feedback & Discussion</h2>
            <p>What did you think of the transition from US to Global data?</p>
        </div>
    </div>

    <div class="visual-stage">
        <div class="sticky-container">
            {#if currentStep === 0}
                <!-- ScrollyMap driven by mapStep, which is updated by innerObserver -->
                <div in:fade out:fade class="chart-box chart-box--map">
                    <Scrollymap bind:mapStep />
                </div>
            {:else if currentStep === 1}
                <div in:fly={{x: 200}} out:fade class="chart-box">
                    <SchoolFunding />
                </div>
            {:else if currentStep === 2}
                <div in:fade out:fade class="chart-box">
                    <ScatterPlot />
                </div>
            {:else if currentStep === 3}
                <div in:fade out:fade class="chart-box viz-3">Finding 3: Scatter Plot Goes Here</div>
            {/if}
        </div>
    </div>
</div>

<style>
    .layout {
        display: flex;
        width: 100%;
    }

    .story {
        width: 40%;
        padding: 0 2rem;
        z-index: 10;
    }

    .header, .footer {
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .step {
        display: flex;
        flex-direction: column;
        justify-content: center;
        opacity: 0.3;
        transition: opacity 0.5s ease;
    }

    .step.active {
        opacity: 1;
    }

    /* Steps 1–3: one viewport height each */
    .step:not(.step-0) {
        height: 100vh;
    }

    /* Step 0 wrapper: height is automatic (sum of sub-steps) */
    .step-0 {
        height: auto;
    }

    /* Each MAP_STEPS sub-step: one viewport height */
    .map-sub-step {
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 1rem 0;
    }

    .step h2 {
        font-size: 2rem;
        color: #2c3e50;
    }

    .step p {
        font-size: 1.25rem;
        line-height: 1.6;
        color: #34495e;
    }

    /* Stat block for map sub-steps */
    .stat-block {
        margin-top: 1.25rem;
        padding: 1rem 1.2rem;
        border-left: 3px solid var(--stat-color, #aaa);
        background: color-mix(in srgb, var(--stat-color, #aaa) 8%, transparent);
        border-radius: 0 6px 6px 0;
    }

    .stat-num {
        display: block;
        font-size: 2.2rem;
        font-weight: 800;
        color: var(--stat-color, #aaa);
        line-height: 1;
        margin-bottom: 0.3rem;
    }

    .stat-label {
        font-size: 0.85rem;
        color: #555;
        line-height: 1.4;
    }

    .visual-stage {
        width: 60%;
    }

    .sticky-container {
        position: sticky;
        top: 0;
        height: 100vh;
        display: grid;
        grid-template-columns: 1fr;
        align-items: center;
        justify-content: center;
        background-color: #ffffff;
        border-left: 1px solid #e0e0e0;
        padding: 1rem;
    }

    .chart-box {
        width: 95%;
        aspect-ratio: 16 / 9;
        max-height: 85vh;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: bold;
        color: white;
        border-radius: 12px;
    }

    .chart-box--map {
       width: 100%;
       aspect-ratio: unset;
       align-self: center;
       display: block;
       height: auto;
    }

    .chart-box--map :global(.map-wrap) {
        width: 100%;
        height: auto;
    }
    .chart-box:not(.chart-box--map) :global(svg) {
        max-width: 100%;
        max-height: 85vh;
    }

    .viz-3 { background-color: #9b59b6; }
</style>
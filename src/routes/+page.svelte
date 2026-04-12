<script>
    import { onMount } from 'svelte';
    import { fade, fly } from 'svelte/transition';
    import ChangeMap from '../components/ChangeMap.svelte';
    import SchoolFunding from '../components/SchoolFunding.svelte';
    import ScatterPlot from '../components/ScatterPlot.svelte';
    import Scrollymap, { STEPS as MAP_STEPS } from '../components/Scrollymap.svelte';
    import MobilityGap from '../components/MobilityGap.svelte';
    import RedistributionDumbbell from '../components/RedistributionDumbbell.svelte';
    import MobilityLeague from '../components/MobilityLeague.svelte';

    let currentStep = $state(0);
    let mapStep = $state(0);
    const useScrollyMap = true;
    const useMilestoneExtras = true;

    const steps = [
        { 
            id: 0, 
            title: "The Geographic Lottery", 
            content: "For children born into low-income families, their adult economic success is highly dependent on their specific county of birth. Why does a zip code matter so much in the U.S.?" 
        },
        { 
            id: 1, 
            title: "Mechanism 1: The Local Funding Trap", 
            content: "Counties do not start with equal public resources. In education, peer countries fund schools more centrally, while the U.S. relies heavily on local tax bases. Poor places collect less, spend less, and pass fewer opportunities to the next generation." 
        },
        { 
            id: 2, 
            title: "Mechanism 2: The Opportunity Gap Inside the U.S.", 
            content: "Across U.S. counties, children from low-income and high-income families do not just start apart - they finish far apart. This confirms that local institutions are not a small detail: they systematically widen inequality in adult outcomes." 
        },
        {
            id: 3,
            title: "Cross-Country Check: Is the U.S. Unusual?",
            content: "GDIM lets us step from county evidence to country-level comparison. Once we place the U.S. beside peers, the pattern is clear: mobility is weaker where inequality is higher, and the U.S. is much closer to low-mobility countries than to Nordic benchmarks."
        },
        {
            id: 4,
            title: "One Story, Two Scales",
            content: "At the county scale, place predicts who climbs. At the country scale, policy predicts whether climbing is common at all. Together, GDIM + inequality data unify the story: weak redistribution turns birthplace into destiny.",
            bridge: "US counties show where mobility fails. GDIM and global policy comparisons show why it fails."
        },
        {
            id: 5,
            title: "Policy Mechanism: Redistribution Dumbbell",
            content: "This view shows how far each country moves from market inequality to disposable inequality. A larger gap means policy is doing more to reduce inequality before families experience final outcomes."
        },
        {
            id: 6,
            title: "Mobility League Table",
            content: "Ranking countries by immobility (IGE) makes the comparison explicit. Lower values mean higher mobility; this benchmark view makes the U.S. position easy to interpret at a glance."
        }
    ];

    const vizGuide = {
        0: "Map guide: scroll the left narrative and hover counties to see adult income rank for children born poor.",
        1: "School funding guide: compare who pays for schools. More local funding means opportunity depends more on local wealth.",
        2: "US opportunity-gap guide: compare county outcomes for poor vs rich children to see how inequality compounds across places.",
        3: "GDIM bridge guide: compare the U.S. with peer countries. X = after-tax inequality, Y = immobility (IGE), bubble size = redistribution gap.",
        4: "Synthesis guide: keep this chart in view and connect the local U.S. mechanisms to cross-country policy patterns.",
        5: "Dumbbell guide: each line is a country from market Gini to disposable Gini; longer lines indicate stronger redistribution.",
        6: "League guide: countries are ranked by immobility (IGE); lower bars indicate higher mobility."
    };

    onMount(() => {
        // ── Outer observer: drives currentStep (which chart to show) ──
        const outerObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    currentStep = parseInt(entry.target.getAttribute('data-step') ?? '0');
                }
            });
        }, { rootMargin: '-50% 0px -50% 0px' });

        document.querySelectorAll('.step').forEach(el => outerObserver.observe(el));

        // ── Inner observer: drives mapStep inside Step 0's sub-steps ──
        const innerObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    mapStep = parseInt(entry.target.getAttribute('data-map-step') ?? '0');
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
            <p class="key-question">Key question: Why does birthplace matter so much in the U.S., and does cross-country evidence suggest policy can change that?</p>
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
                {#if step.bridge}
                    <div class="bridge-note">{step.bridge}</div>
                {/if}
            </div>
        {/each}

        <div class="footer">
            <h2>Feedback & Discussion</h2>
            <p>Did the GDIM bridge make the transition from U.S. local evidence to global policy evidence feel coherent?</p>
        </div>
    </div>

    <div class="visual-stage">
        <div class="sticky-container">
            <div class="viz-guide">{vizGuide[currentStep] ?? vizGuide[0]}</div>
            {#if currentStep === 0}
                <!-- ScrollyMap driven by mapStep, which is updated by innerObserver -->
                <div in:fade out:fade class="chart-box chart-box--map">
                    {#if useScrollyMap}
                        <Scrollymap bind:mapStep />
                    {:else}
                        <ChangeMap />
                    {/if}
                </div>
            {:else if currentStep === 1}
                <div in:fly={{x: 200}} out:fade class="chart-box">
                    <SchoolFunding />
                </div>
            {:else if currentStep === 2}
                <div in:fade out:fade class="chart-box">
                    <ScatterPlot />
                </div>
            {:else if currentStep === 3 || currentStep === 4}
                <div in:fade out:fade class="chart-box chart-box--tall">
                    <MobilityGap />
                </div>
            {:else if currentStep === 5}
                <div in:fade out:fade class="chart-box chart-box--tall">
                    {#if useMilestoneExtras}
                        <RedistributionDumbbell />
                    {:else}
                        <MobilityGap />
                    {/if}
                </div>
            {:else if currentStep >= 6}
                <div in:fade out:fade class="chart-box chart-box--tall">
                    {#if useMilestoneExtras}
                        <MobilityLeague />
                    {:else}
                        <MobilityGap />
                    {/if}
                </div>
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

    .key-question {
        margin-top: 1rem;
        max-width: 36ch;
        font-size: 0.95rem;
        color: #5e6f77;
        line-height: 1.45;
        font-weight: 500;
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

    /* Step 0 wrapper: height is automatic */
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

    .bridge-note {
        margin-top: 1rem;
        padding: 0.8rem 1rem;
        border-left: 3px solid #1a8a5a;
        background: rgba(26, 138, 90, 0.08);
        color: #28553e;
        font-size: 0.95rem;
        line-height: 1.4;
        border-radius: 0 8px 8px 0;
        max-width: 38ch;
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

    .viz-guide {
        position: absolute;
        top: 0.75rem;
        left: 1rem;
        right: 1rem;
        z-index: 2;
        font-size: 0.8rem;
        line-height: 1.35;
        color: #4b5a64;
        background: rgba(248, 250, 251, 0.9);
        border: 1px solid #e4eaee;
        border-radius: 8px;
        padding: 0.55rem 0.7rem;
        backdrop-filter: blur(2px);
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

    .chart-box--tall {
        aspect-ratio: 4 / 3;
        max-height: 90vh;
    }

    .chart-box:not(.chart-box--map) :global(svg) {
        max-width: 100%;
        max-height: 85vh;
    }

    @media (max-width: 1024px) {
        .layout {
            flex-direction: column;
        }

        .story,
        .visual-stage {
            width: 100%;
        }

        .story {
            padding: 0 1rem;
        }

        .sticky-container {
            position: relative;
            top: auto;
            min-height: 70vh;
            height: auto;
            border-left: 0;
            border-top: 1px solid #e0e0e0;
            padding-top: 3rem;
        }

        .chart-box {
            width: 100%;
            max-height: none;
        }

        .chart-box:not(.chart-box--map) :global(svg) {
            max-height: none;
        }
    }

</style>
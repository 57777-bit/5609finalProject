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
    const useMilestoneExtras = true;

    /* ── Auto-play state for Step 0 ── */
    let autoPlayDone = $state(false);
    let autoPlayTimer = null;
    let heroVisible = $state(false);
    let autoPlaying = false;  /* lock to prevent observer from changing currentStep */

    /* ─────────────────────────────────────────────
       NEW NARRATIVE STRUCTURE
       Act I  (US county data):  Steps 0 → 1 → 2
       Bridge (funding):         Step 3
       Act II (global data):     Steps 4 → 5 → 6
       ───────────────────────────────────────────── */
    const steps = [
        /* ── Act I: The American Problem ── */
        {
            id: 0,
            title: "The Geographic Lottery",
            content: "For children born into low-income families, their adult economic success is highly dependent on their specific county of birth. Why does a zip code matter so much in the U.S.?",
            transition: ""
        },
        {
            id: 1,
            title: "The Privilege Shield",
            content: "Geography punishes the poor far more than it constrains the rich. Across U.S. counties, children from wealthy families end up near the top almost everywhere. For children born poor, the county they're born in makes all the difference.",
            transition: "If where you're born locks in your fate, is the lock at least loosening over time?"
        },
        {
            id: 2,
            title: "A Fading Dream",
            content: "The answer is no. Comparing children born in 1978 with those born in 1992, upward mobility has declined in many counties — especially in the South and Midwest. The American Dream is fading fastest in the places that needed it most.",
            transition: "Three facts from U.S. county data: birthplace predicts destiny, wealth insulates, and the problem is getting worse. But why? One concrete clue lies in how America funds its schools."
        },

        /* ── Bridge: From U.S. mechanism to global lens ── */
        {
            id: 3,
            title: "The Local Funding Trap",
            content: "In most developed countries, schools are funded centrally — every child gets similar resources. In the U.S., 91% of education funding comes from local taxes. Poor places collect less, spend less, and pass fewer opportunities to the next generation.",
            transition: "Education funding is one mechanism, but it points to a larger pattern. Do countries with more unequal societies systematically produce less mobility? Let's zoom out."
        },

        /* ── Act II: The Global Perspective ── */
        {
            id: 4,
            title: "The Global Pattern",
            content: "Plotting inequality against immobility for dozens of countries reveals a clear relationship: the more unequal a society, the harder it is to climb. The U.S. sits with high inequality and low mobility — far from Nordic benchmarks.",
            transition: "What separates high-mobility countries from the rest? The answer is redistribution — how much policy intervenes between market outcomes and what families actually experience."
        },
        {
            id: 5,
            title: "The Redistribution Gap",
            content: "Each line shows how far a country moves from market inequality to after-tax inequality. Nordic countries cut their Gini by 20+ points through taxes and transfers. The U.S. barely moves the needle.",
            transition: "Putting it all together — where does the U.S. rank among its peers?"
        },
        {
            id: 6,
            title: "Where America Stands",
            content: "Ranked by intergenerational immobility, the U.S. falls near the bottom of developed nations. Higher mobility is not a mystery — it exists in countries that chose different policies.",
            transition: ""
        }
    ];

    const vizGuide = {
        0: "Watch how birthplace shapes opportunity — the map reveals itself automatically.",
        1: "Compare county outcomes: X-axis = children born poor, Y-axis = children born rich. Points far from the diagonal show large gaps.",
        2: "Blue counties = mobility improved (1978→1992). Red counties = mobility worsened. Toggle views to compare.",
        3: "Compare who pays for schools: blue = central/federal funding, red = local/state funding.",
        4: "Each bubble is a country. X = inequality (Gini), Y = immobility (IGE). The U.S. is highlighted.",
        5: "Each line spans from market Gini to disposable Gini. Longer lines = stronger redistribution.",
        6: "Countries ranked by immobility (IGE). Lower bars = higher mobility. U.S. highlighted in red."
    };

    function startAutoPlay() {
        if (autoPlayDone || autoPlayTimer) return;
        autoPlaying = true;
        currentStep = 0;
        mapStep = 0;

        const schedule = [
            { delay: 2500, step: 1 },
            { delay: 6000, step: 2 },
            { delay: 9500, step: 3 },
        ];

        schedule.forEach(({ delay, step }) => {
            setTimeout(() => {
                mapStep = step;
            }, delay);
        });

        autoPlayTimer = setTimeout(() => {
            autoPlayDone = true;
            autoPlaying = false;
            autoPlayTimer = null;
        }, 12500);
    }

    onMount(() => {
        heroVisible = true;
        currentStep = 0;

        /* Use a tick delay so Svelte has rendered the DOM */
        requestAnimationFrame(() => {
            const outerObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const step = parseInt(entry.target.getAttribute('data-step') ?? '0');
                        /* During auto-play, lock currentStep to 0 so the map stays visible */
                        if (autoPlaying) {
                            if (step === 0) currentStep = 0;
                            return;
                        }
                        currentStep = step;
                        if (step === 0 && !autoPlayDone) startAutoPlay();
                    }
                });
            }, { rootMargin: '-30% 0px -30% 0px' });

            document.querySelectorAll('.step').forEach(el => outerObserver.observe(el));
        });

        startAutoPlay();

        return () => {
            if (autoPlayTimer) clearTimeout(autoPlayTimer);
        };
    });
</script>

<div class="layout">
    <div class="story">
        <div class="header" class:visible={heroVisible}>
            <h1>The Geography of Opportunity</h1>
            <p class="subtitle">A data story about birthplace, mobility, and policy</p>
            <p class="key-question">Key question: Why does birthplace matter so much in the U.S., and does cross-country evidence suggest policy can change that?</p>
        </div>

        <!-- ── Step 0: Auto-play map narration ── -->
        <div class="step step-0-auto" data-step={0} class:active={currentStep === 0}>
            <div class="auto-narration">
                {#each MAP_STEPS as stepDef (stepDef.id)}
                    <div class="narration-card" class:card-visible={mapStep >= stepDef.id}>
                        <h2>{stepDef.title}</h2>
                        <p>{stepDef.content}</p>
                        {#if stepDef.statNum}
                            <div class="stat-block" style="--stat-color: {stepDef.statColor}">
                                <span class="stat-num">{stepDef.statNum}</span>
                                <span class="stat-label">{stepDef.statLabel}</span>
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
            <!-- Scroll guide after auto-play -->
            {#if autoPlayDone}
                <div class="scroll-guide" in:fade>
                    <div class="scroll-guide-line"></div>
                    <p>But geography is only the beginning of the story</p>
                    <p class="scroll-guide-hint">Scroll down to explore why ↓</p>
                    <div class="scroll-guide-arrow">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#e67e22" stroke-width="2"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
                    </div>
                </div>
            {/if}
        </div>

        <!-- ── Steps 1–6: scrollytelling with transitions ── -->
        {#each steps.slice(1) as step}
            <div class="step" data-step={step.id} class:active={currentStep === step.id}>
                <h2>{step.title}</h2>
                <p>{step.content}</p>
                {#if step.transition}
                    <div class="transition-note">{step.transition}</div>
                {/if}

                <!-- Act divider labels -->
                {#if step.id === 1}
                    <div class="act-label">Part I — The American Problem</div>
                {/if}
                {#if step.id === 4}
                    <div class="act-label">Part II — The Global Perspective</div>
                {/if}
            </div>
        {/each}

        <div class="footer">
            <h2>The Bottom Line</h2>
            <p>Birthplace determines destiny — but it doesn't have to. The counties where poor children stay stuck, the widening gap over time, and America's outlier status among developed nations all point to the same conclusion: this is a policy choice, not an inevitability.</p>
            <p class="footer-sub">Countries that invest in universal education funding, progressive taxation, and social transfers have cracked the code. The question is whether America will choose to follow.</p>
        </div>
    </div>

    <div class="visual-stage">
        <div class="sticky-container">
            <div class="viz-guide">{vizGuide[currentStep] ?? vizGuide[0]}</div>

            {#if currentStep === 0}
                <!-- Act I, Step 0: Scrollymap auto-play -->
                <div in:fade out:fade class="chart-box chart-box--map">
                    <Scrollymap bind:mapStep />
                </div>
            {:else if currentStep === 1}
                <!-- Act I, Step 1: ScatterPlot (poor vs rich) -->
                <div in:fade out:fade class="chart-box">
                    <ScatterPlot />
                </div>
            {:else if currentStep === 2}
                <!-- Act I, Step 2: ChangeMap (1978→1992) -->
                <div in:fade out:fade class="chart-box chart-box--map">
                    <ChangeMap />
                </div>
            {:else if currentStep === 3}
                <!-- Bridge, Step 3: SchoolFunding -->
                <div in:fly={{x: 200}} out:fade class="chart-box">
                    <SchoolFunding />
                </div>
            {:else if currentStep === 4}
                <!-- Act II, Step 4: MobilityGap bubble chart -->
                <div in:fade out:fade class="chart-box chart-box--tall">
                    <MobilityGap />
                </div>
            {:else if currentStep === 5}
                <!-- Act II, Step 5: Redistribution Dumbbell -->
                <div in:fade out:fade class="chart-box chart-box--tall">
                    {#if useMilestoneExtras}
                        <RedistributionDumbbell />
                    {:else}
                        <MobilityGap />
                    {/if}
                </div>
            {:else if currentStep >= 6}
                <!-- Act II, Step 6: Mobility League -->
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

    .header {
        height: 70vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        opacity: 0;
        transform: translateY(30px);
        transition: opacity 1s ease, transform 1s ease;
    }
    .header.visible {
        opacity: 1;
        transform: translateY(0);
    }

    .subtitle {
        font-size: 1.1rem;
        color: #5e6f77;
        margin-top: 0.3rem;
    }

    .key-question {
        margin-top: 1rem;
        max-width: 36ch;
        font-size: 0.95rem;
        color: #5e6f77;
        line-height: 1.45;
        font-weight: 500;
    }

    .footer {
        min-height: 60vh;
        padding: 4rem 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .footer h2 {
        font-size: 2rem;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }

    .footer p {
        font-size: 1.25rem;
        line-height: 1.6;
        color: #34495e;
        max-width: 40ch;
    }

    .footer-sub {
        margin-top: 1rem;
        font-size: 1rem \!important;
        color: #5e6f77 \!important;
        font-style: italic;
    }

    .step {
        display: flex;
        flex-direction: column;
        justify-content: center;
        opacity: 0.25;
        transition: opacity 0.5s ease;
    }

    .step.active {
        opacity: 1;
    }

    /* Step 0 always visible during auto-play */
    .step-0-auto {
        opacity: 1 \!important;
    }

    .step:not(.step-0-auto) {
        min-height: 60vh;
        padding: 3rem 0;
    }

    /* ── Step 0 auto-play ── */
    .step-0-auto {
        min-height: auto;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 2rem 0;
    }

    .auto-narration {
        display: flex;
        flex-direction: column;
    }

    .narration-card {
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transform: translateY(20px);
        transition: max-height 0.8s cubic-bezier(0.4, 0, 0.2, 1),
                    opacity 0.8s ease,
                    transform 0.8s ease,
                    padding 0.8s ease,
                    margin 0.8s ease;
        padding: 0;
        margin: 0;
    }

    .narration-card.card-visible {
        max-height: 400px;
        opacity: 1;
        transform: translateY(0);
        padding: 1rem 0;
        margin-bottom: 0.5rem;
    }

    .narration-card h2 {
        font-size: 1.6rem;
        color: #2c3e50;
        margin-bottom: 0.4rem;
    }

    .narration-card p {
        font-size: 1.1rem;
        line-height: 1.5;
        color: #34495e;
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

    /* ── Scroll guide after auto-play ── */
    .scroll-guide {
        text-align: center;
        margin-top: 2rem;
        padding: 2rem 0;
    }

    .scroll-guide p {
        font-size: 1.1rem;
        color: #555;
        margin: 0.3rem 0;
    }

    .scroll-guide-line {
        width: 1px;
        height: 40px;
        background: #ccc;
        margin: 0 auto 1rem;
    }

    .scroll-guide-hint {
        font-size: 0.9rem \!important;
        color: #e67e22 \!important;
        font-weight: 600;
    }

    .scroll-guide-arrow {
        margin-top: 0.5rem;
        animation: bounceDown 1.5s infinite;
    }

    @keyframes bounceDown {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(8px); }
    }

    /* ── Transition notes ── */
    .transition-note {
        margin-top: 1.5rem;
        padding: 1rem 1.2rem;
        font-size: 0.95rem;
        line-height: 1.5;
        color: #b45309;
        font-style: italic;
        border-left: 3px solid #f59e0b;
        background: rgba(245, 158, 11, 0.06);
        border-radius: 0 6px 6px 0;
    }

    /* ── Act labels ── */
    .act-label {
        margin-top: 2rem;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #94a3b8;
    }

    /* ── Stat blocks ── */
    .stat-block {
        margin-top: 0.8rem;
        padding: 0.8rem 1rem;
        border-left: 3px solid var(--stat-color, #aaa);
        background: color-mix(in srgb, var(--stat-color, #aaa) 8%, transparent);
        border-radius: 0 6px 6px 0;
    }

    .stat-num {
        display: block;
        font-size: 2rem;
        font-weight: 800;
        color: var(--stat-color, #aaa);
        line-height: 1;
        margin-bottom: 0.2rem;
    }

    .stat-label {
        font-size: 0.85rem;
        color: #555;
        line-height: 1.4;
    }

    /* ── Right panel ── */
    .visual-stage {
        width: 60%;
        position: relative;
    }

    .sticky-container {
        position: sticky;
        top: 0;
        height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: #fff;
        border-left: 1px solid #e0e0e0;
        padding: 1rem;
    }

    .viz-guide {
        position: absolute;
        top: 0.75rem;
        left: 1rem;
        right: 1rem;
        font-size: 0.8rem;
        line-height: 1.35;
        color: #4b5a64;
        background: rgba(248, 250, 251, 0.9);
        border: 1px solid #e4eaee;
        border-radius: 8px;
        padding: 0.55rem 0.7rem;
        z-index: 5;
    }

    .chart-box {
        width: 90%;
        aspect-ratio: 4 / 3;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .chart-box--map {
        width: 95%;
        aspect-ratio: auto;
    }

    .chart-box--tall {
        aspect-ratio: 3 / 4;
    }

    /* ── Mobile / narrow screens ── */
    @media (max-width: 1024px) {
        .layout {
            flex-direction: column;
        }
        .story {
            width: 100%;
            padding: 0 1rem;
        }
        .visual-stage {
            width: 100%;
        }
        .sticky-container {
            position: relative;
            height: auto;
            min-height: 50vh;
        }
        .header {
            height: auto;
            min-height: 40vh;
        }
    }

    h1 {
        font-size: 2.5rem;
        color: #2c3e50;
        margin-bottom: 0.3rem;
    }
</style>

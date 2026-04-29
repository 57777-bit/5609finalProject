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
    import Mobility3D from '../components/Mobility3D.svelte';

    let currentStep = $state(0);
    let mapStep = $state(0);
    const useMilestoneExtras = true;

    /* ── Auto-play state for Step 0 ── */
    let autoPlayDone = $state(false);
    let autoPlayTimer = null;
    let heroVisible = $state(false);
    let autoPlaying = $state(false);  /* drives Play / Replay button visibility + scroll-lock during animation */

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
            content: "For children born into low-income families, where they grow up shapes who they become as adults. In the U.S., a county of birth can decide a lifetime.",
            transition: ""
        },
        {
            id: 1,
            title: "The Privilege Shield",
            content: "Each dot on the right is a U.S. county. The dashed line is where poor and rich children would end up at the same percentile — perfect equal opportunity. Instead, the cloud sags far below it. The labelled red dots are counties where being born poor cuts a child's adult percentile by 50 points or more. Geography barely touches kids born rich; it crushes kids born poor.",
            transition: "So geography traps poor kids. But is this getting better or worse over time?"
        },
        {
            id: 2,
            title: "A Fading Dream",
            content: "Hit ▶ Play to compare two cohorts: kids born in 1978 against kids born in 1992. Watch the red bloom across the regions labelled SOUTH and MIDWEST — counties where the younger generation has worse mobility than their parents. The places that already had the least opportunity lost more.",
            transition: "Three facts from U.S. county data: birthplace predicts destiny, wealth insulates, and the problem is getting worse. Why? One concrete clue lies in how America funds its schools."
        },

        /* ── Bridge: From U.S. mechanism to global lens ── */
        {
            id: 3,
            title: "The Local Funding Trap",
            content: "Compare the bars on the right: blue is central or federal funding, red is local property-tax funding. The U.S. row is almost entirely red — about 91% of K–12 funding is raised locally. Norway, Sweden, and Japan are the opposite. When schooling depends on the wealth of the surrounding ZIP code, poor places stay poor.",
            transition: "Education funding is one mechanism, but it points to a larger pattern. Do unequal societies systematically produce less mobility? Let's zoom out."
        },

        /* ── Act II: The Global Perspective ── */
        {
            id: 4,
            title: "The Global Pattern",
            content: "Each bubble is a country. X-axis: how unequal incomes are after taxes. Y-axis: how immobile children are between generations. The dashed trendline slopes up — more inequality, less mobility. The red dot in the upper right is the U.S. The green NORDIC BENCHMARKS cluster sits in the opposite corner: less unequal, more mobile.",
            transition: "What separates high-mobility countries from the rest? The answer is redistribution — how much policy intervenes between market outcomes and what families actually live."
        },
        {
            id: 5,
            title: "The Redistribution Gap",
            content: "Each line spans from market Gini (orange) to after-tax Gini (blue) — the longer the line, the more taxes and transfers compress inequality. The green Nordic lines drop by 20+ points. The U.S. line is short: market inequality is barely softened by policy.",
            transition: "Putting it all together — where does the U.S. rank among its peers?"
        },
        {
            id: 6,
            title: "Where America Stands",
            content: "The chart on the right ranks twenty major economies by intergenerational immobility — shorter bars mean kids escape their parents' income bracket more easily. The U.S. sits at rank 10, with nine wealthy peers above it: Canada, Australia, Sweden, Finland, the United Kingdom, Japan, Korea, the Netherlands, and Switzerland. Every one of them gives their poor children a better shot than America does. The four highlighted in deep blue (Canada, Sweden, the United Kingdom, Japan) are the most-cited cultural benchmarks.",
            transition: "Finally, a 3D look at the same county-level mobility data. Drag the scene to orbit, scroll to zoom — the column heights are mobility itself, so the country's terrain literally becomes a topography of opportunity."
        },

        /* ── Bonus: 3D extruded mobility map ── */
        {
            id: 7,
            title: "A Topography of Opportunity",
            content: "Each column is a U.S. county; its height is upward mobility for children of poor parents (1992 cohort). The mountains and the valleys aren't terrain — they're the same county-level mobility you saw in the opening map, recast as something you can walk around. Drag to orbit, scroll to zoom. Tall blue ridges = places where poor children climb; short red basins = places where they don't.",
            transition: ""
        }
    ];

    const vizGuide = {
        0: "Watch the map animate through three stages of mobility — then switch to 'State bubble map' and click any state to zoom into its counties. Smaller states like those in the Northeast are easier to explore this way.",
        1: "Hover over any dot to see the exact mobility gap for that county — how far apart outcomes are for kids born poor vs. born rich in the same place.",
        2: "Hit ▶ Play to see how mobility shifted between 1978 and 1992. Counties with the biggest changes appear first — watch where the red spreads.",
        3: "Compare who pays for schools: blue = central/federal funding, red = local/state funding.",
        4: "Each bubble is a country. X = inequality (Gini), Y = immobility (IGE). The U.S. is highlighted.",
        5: "Each line spans from market Gini to disposable Gini. Longer lines = stronger redistribution.",
        6: "Countries ranked by immobility (IGE). Lower bars = higher mobility. U.S. highlighted in red.",
        7: "Drag the canvas to orbit the 3D scene. Scroll to zoom. Hover any column for the county name and exact mobility value."
    };

    function scrollToCard(stepId) {
        setTimeout(() => {
            const cards = document.querySelectorAll('.narration-card');
            if (cards[stepId]) {
                cards[stepId].scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 200);
    }

    let autoPlayTimers = [];

    function startAutoPlay() {
        if (autoPlaying) return;
        autoPlaying = true;
        autoPlayDone = false;
        currentStep = 0;
        mapStep = 0;

        const schedule = [
            { delay: 3500, step: 1 },
            { delay: 7000, step: 2 },
            { delay: 10500, step: 3 },
        ];

        schedule.forEach(({ delay, step }) => {
            const t = setTimeout(() => {
                mapStep = step;
            }, delay);
            autoPlayTimers.push(t);
        });

        const tDone = setTimeout(() => {
            autoPlayDone = true;
            autoPlaying = false;
        }, 13500);
        autoPlayTimers.push(tDone);
    }

    function replayAutoPlay() {
        autoPlayTimers.forEach(t => clearTimeout(t));
        autoPlayTimers = [];
        autoPlayDone = false;
        autoPlaying = false;
        mapStep = 0;
        // small tick so the DOM observes the reset before re-firing
        setTimeout(() => startAutoPlay(), 60);
    }

    onMount(() => {
        heroVisible = true;
        currentStep = 0;

        let scrollPending = false;
        let stepEls = [];

        // Pure function of current scroll position: which step element
        // contains the viewport-center reference line. Deterministic and
        // direction-agnostic, so scrolling up gives the same answer as
        // scrolling down through the same Y.
        function computeActiveStep() {
            const refY = window.innerHeight / 2;
            let insideId = -1;
            let closestId = 0;
            let closestDist = Infinity;

            for (const el of stepEls) {
                const rect = el.getBoundingClientRect();
                const id = parseInt(el.getAttribute('data-step') ?? '0');
                if (rect.top <= refY && rect.bottom >= refY) insideId = id;
                const center = (rect.top + rect.bottom) / 2;
                const dist = Math.abs(center - refY);
                if (dist < closestDist) {
                    closestDist = dist;
                    closestId = id;
                }
            }
            return insideId !== -1 ? insideId : closestId;
        }

        // Step tracking is purely scroll-position-based. The Step 0 map
        // animation is NEVER auto-triggered from scroll — it only fires
        // when the user clicks the explicit ▶ Play button. This avoids
        // the fast-scroll race conditions that plagued the previous build.
        function updateActiveStep() {
            const next = computeActiveStep();
            if (autoPlaying) {
                // Keep the right panel pinned to the Scrollymap while the
                // animation is running, so scrolling can't yank the chart
                // out from under the reveal.
                if (next === 0) currentStep = 0;
                return;
            }
            if (next !== currentStep) currentStep = next;
        }

        function onScroll() {
            if (scrollPending) return;
            scrollPending = true;
            requestAnimationFrame(() => {
                scrollPending = false;
                updateActiveStep();
            });
        }

        requestAnimationFrame(() => {
            stepEls = Array.from(document.querySelectorAll('.step'));
            window.addEventListener('scroll', onScroll, { passive: true });
            window.addEventListener('resize', onScroll);
            updateActiveStep();
        });

        return () => {
            autoPlayTimers.forEach(t => clearTimeout(t));
            window.removeEventListener('scroll', onScroll);
            window.removeEventListener('resize', onScroll);
        };
    });
</script>

<!-- ── Full-screen hero ── -->
<section class="hero" class:visible={heroVisible}>
    <div class="hero-inner">
        <p class="hero-eyebrow">A data story</p>
        <h1>The Geography<br>of Opportunity</h1>
        <p class="hero-sub">Birthplace, mobility, and policy</p>
        <p class="hero-question">Why does a zip code matter so much in the U.S., and does cross-country evidence suggest policy can change that?</p>
        <div class="hero-scroll-hint">
            <span>Scroll to explore</span>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 4v12M5 11l5 5 5-5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
    </div>
</section>

<div class="layout">
    <div class="story">

        <!-- ── Step 0: Button-triggered map narration ── -->
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

            <!-- Play button: explicit user trigger, never scroll-driven -->
            {#if !autoPlaying && !autoPlayDone}
                <div class="play-button-wrap" in:fade>
                    <button class="play-button" onclick={startAutoPlay} aria-label="Play the map animation">
                        <span class="play-icon">▶</span>
                        <span class="play-label">Play the map animation</span>
                    </button>
                    <p class="play-hint">Click to watch how mobility maps onto American geography</p>
                </div>
            {/if}

            <!-- Live progress indicator while playing -->
            {#if autoPlaying}
                <div class="play-status" in:fade>
                    <span class="play-status-dot"></span>
                    <span>Playing... {mapStep + 1} of {MAP_STEPS.length}</span>
                </div>
            {/if}

            <!-- After-play scroll guide + replay -->
            {#if autoPlayDone}
                <div class="scroll-guide" in:fade>
                    <button class="replay-button" onclick={replayAutoPlay} aria-label="Replay the map animation">
                        <span>↻ Replay animation</span>
                    </button>
                    <div class="scroll-guide-line"></div>
                    <p>But geography is only the beginning of the story</p>
                    <p class="scroll-guide-hint">Scroll down to explore why</p>
                    <div class="scroll-guide-hand">
                        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <!-- Hand pointing down -->
                            <path d="M24 4C23 4 22 5 22 6V26L18.7 22.7C17.9 21.9 16.6 21.9 15.8 22.7C15 23.5 15 24.8 15.8 25.6L22.6 32.4C23.4 33.2 24.6 33.2 25.4 32.4L32.2 25.6C33 24.8 33 23.5 32.2 22.7C31.4 21.9 30.1 21.9 29.3 22.7L26 26V6C26 5 25 4 24 4Z" fill="#e63946"/>
                            <!-- Down arrows below hand -->
                            <path d="M18 36l6 6 6-6" stroke="#e63946" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                            <path d="M18 30l6 6 6-6" stroke="#e63946" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none" opacity="0.5"/>
                        </svg>
                    </div>
                </div>
            {/if}
        </div>

        <!-- ── Steps 1–6: scrollytelling with transitions ── -->
        {#each steps.slice(1) as step}
            <div class="step" data-step={step.id} class:active={currentStep === step.id}>
                <h2>{step.title}</h2>
                <p>{step.content}</p>
                {#if step.finding}
                    <div class="finding-block">
                        <strong>Key finding:</strong> {step.finding}
                    </div>
                {/if}
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
            <p>Look at the rank chart still on the right. Nine wealthy peers sit above the red U.S. bar — <strong>Canada, Sweden, the United Kingdom, Japan</strong> (marked in deep blue), plus Australia, Finland, Korea, the Netherlands, and Switzerland. Every one of them gives their poor children a better shot than America does. The gap is not destiny: those countries pay for schools, tax incomes, and support families differently than the U.S. does.</p>
            <p class="footer-sub">Birthplace shapes a child's life — in the U.S. especially so — but the international ranking shows the ceiling can be moved by countries with comparable means. The question is which of those choices America is willing to copy.</p>
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
                <div in:fade out:fade class="chart-box chart-box--changemap">
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
            {:else if currentStep === 6}
                <!-- Act II, Step 6: Mobility League -->
                <div in:fade out:fade class="chart-box chart-box--tall">
                    {#if useMilestoneExtras}
                        <MobilityLeague />
                    {:else}
                        <MobilityGap />
                    {/if}
                </div>
            {:else if currentStep >= 7}
                <!-- Bonus Step 7: 3D extruded mobility map (deck.gl) -->
                <div in:fade out:fade class="chart-box chart-box--tall">
                    <Mobility3D />
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

    /* ── Hero ── */
    .hero {
        height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #fff;
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 1s ease, transform 1s ease;
    }
    .hero.visible {
        opacity: 1;
        transform: translateY(0);
    }
    .hero-inner {
        text-align: center;
        max-width: 640px;
        padding: 2rem;
    }
    .hero-eyebrow {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #e63946;
        margin-bottom: 1rem;
    }
    .hero-inner h1 {
        font-size: clamp(2.8rem, 6vw, 5rem);
        color: #2c3e50;
        line-height: 1.1;
        margin-bottom: 1rem;
    }
    .hero-sub {
        font-size: 1.1rem;
        color: #5e6f77;
        margin-bottom: 1.5rem;
    }
    .hero-question {
        font-size: 1rem;
        color: #5e6f77;
        line-height: 1.6;
        max-width: 48ch;
        margin: 0 auto 2.5rem;
        font-weight: 500;
    }
    .hero-scroll-hint {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.4rem;
        font-size: 0.85rem;
        color: #94a3b8;
        animation: bounceDown 1.8s ease-in-out infinite;
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
        /* Match step height (100vh) so footer text spans the same vertical
           extent as the sticky chart in the right panel.
           justify-content: flex-start (instead of center) keeps the heading
           anchored to the top of the viewport — same y position as the
           sticky chart card's top — so chart and text read as one row
           instead of "chart floating above, text drifting below". */
        min-height: 100vh;
        padding: 4rem 0;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
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
        min-height: 100vh;
        padding: 4rem 0;
    }

    /* ── Step 0 button-triggered narration ── */
    /* Lock to 100vh so layout never reflows mid-scroll: the section
       always occupies one full screen, regardless of how many narration
       cards are revealed. This prevents the fast-scroll race where the
       section was ~150px tall before play and ~900px during play. */
    .step-0-auto {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 4rem 0;
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

    .scroll-guide-main {
        font-size: 1.15rem \!important;
        color: #2c3e50 \!important;
        font-weight: 500;
    }

    .scroll-guide-cta {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.6rem;
        margin-top: 1rem;
        padding: 0.8rem 2rem;
        background: rgba(230, 57, 70, 0.1);
        border: 2.5px solid #e63946;
        border-radius: 30px;
        animation: ctaPulse 2s ease-in-out infinite;
    }

    .scroll-guide-icon {
        font-size: 2.2rem;
        line-height: 1;
    }

    .scroll-guide-hint {
        font-size: 1.15rem \!important;
        color: #e63946 \!important;
        font-weight: 700;
        margin: 0 \!important;
    }

    @keyframes ctaPulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(230, 57, 70, 0.3); }
        50% { box-shadow: 0 0 0 10px rgba(230, 57, 70, 0); }
    }

    .scroll-guide-arrows {
        margin-top: 0.5rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        animation: bounceDown 1.2s ease-in-out infinite;
    }

    @keyframes bounceDown {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(12px); }
    }

    /* ── Play / Replay buttons (Step 0 manual trigger) ── */
    .play-button-wrap {
        margin-top: 2rem;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 0.5rem;
    }

    .play-button {
        display: inline-flex;
        align-items: center;
        gap: 0.7rem;
        padding: 0.95rem 2.2rem;
        background: #e63946;
        color: #fff;
        border: none;
        border-radius: 30px;
        font-size: 1.05rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 16px rgba(230, 57, 70, 0.28);
        transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
        animation: playPulse 2.4s ease-in-out infinite;
    }
    .play-button:hover {
        background: #d62839;
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(230, 57, 70, 0.4);
    }
    .play-button:active {
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(230, 57, 70, 0.35);
    }
    .play-icon {
        font-size: 0.95rem;
        line-height: 1;
    }
    .play-label {
        letter-spacing: 0.01em;
    }
    .play-hint {
        font-size: 0.85rem \!important;
        color: #7b8a8b \!important;
        margin: 0 \!important;
        max-width: 36ch;
    }
    @keyframes playPulse {
        0%, 100% { box-shadow: 0 4px 16px rgba(230, 57, 70, 0.28); }
        50%      { box-shadow: 0 4px 16px rgba(230, 57, 70, 0.28), 0 0 0 8px rgba(230, 57, 70, 0.10); }
    }

    .play-status {
        margin-top: 1.4rem;
        display: inline-flex;
        align-items: center;
        gap: 0.55rem;
        font-size: 0.9rem;
        color: #5e6f77;
        font-weight: 500;
    }
    .play-status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #e63946;
        animation: dotBlink 1s ease-in-out infinite;
    }
    @keyframes dotBlink {
        0%, 100% { opacity: 1; }
        50%      { opacity: 0.25; }
    }

    .replay-button {
        background: transparent;
        color: #e63946;
        border: 2px solid #e63946;
        padding: 0.55rem 1.4rem;
        border-radius: 24px;
        font-size: 0.92rem;
        font-weight: 600;
        cursor: pointer;
        margin-bottom: 1.2rem;
        transition: background 0.15s ease, color 0.15s ease, transform 0.15s ease;
    }
    .replay-button:hover {
        background: #e63946;
        color: #fff;
        transform: translateY(-1px);
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
        display: grid;
        place-items: center;
        background: #fff;
        border-left: 1px solid #e0e0e0;
        padding: 1rem;
        overflow: hidden;
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
        grid-area: 1 / 1;
        width: 90%;
        max-height: 85vh;
        aspect-ratio: 4 / 3;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 0;
        min-height: 0;
    }

    .chart-box--map {
        width: 95%;
        aspect-ratio: unset;
        height: auto;
    }

    .chart-box--tall {
        width: 90%;
        max-width: 60vh;
        height: auto;
        aspect-ratio: 3 / 4;
    }

    .chart-box--changemap {
        width: 100%;
        height: auto;
        aspect-ratio: unset;
        align-self: stretch;
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

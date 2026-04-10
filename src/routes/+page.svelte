<script>
    import { onMount } from 'svelte';
    import EducationMobility from '../components/EducationMobility.svelte';
    import { fade, fly } from 'svelte/transition';

    // Svelte 5 Rune to track which section is currently active
    let currentStep = $state(0);

    // Your narrative sections. We can add the new Education data here later.
    const steps = [
        { id: 0, title: "The Geographic Lottery", content: "For children born into low-income families, their adult economic success is highly dependent on their specific county of birth." },
        { id: 1, title: "The Missing Link: Education", content: "Why do some countries overcome this lottery? Looking globally, the U.S. has a remarkably high starting point for parental education, but one of the smallest mobility gaps for children compared to Nordic peers." },
        { id: 2, title: "The Redistribution Gap", content: "Before taxes and transfers, most developed countries have similar levels of market inequality; the primary differentiator is government policy." },
        { id: 3, title: "What Inequality Costs", content: "High levels of income concentration at the top are strongly associated with lower life expectancies." }
    ];

    onMount(() => {
        // This observer triggers when a text block hits the exact vertical center of the screen
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
                <div in:fade out:fade class="chart-box viz-1">Finding 1: US Maps Go Here</div>
            {:else if currentStep === 1}
                <div in:fly={{x: 200}} out:fade class="chart-box">
                    <EducationMobility />
                </div>
            {:else if currentStep === 2}
                <div in:fade out:fade class="chart-box viz-2">Finding 2: Slopegraph Goes Here</div>
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

    /* Left Column */
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
        height: 100vh; /* Forces user to scroll to see the next point */
        display: flex;
        flex-direction: column;
        justify-content: center;
        opacity: 0.3; /* Dims text that isn't currently focused */
        transition: opacity 0.5s ease;
    }

    .step.active {
        opacity: 1; /* Highlights the text currently in the middle of the screen */
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

    /* Right Column (Sticky Sidecar) */
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

    /* Temporary placeholders for your groupmates */
    .chart-box {
        width: 95%;
        aspect-ratio: 16 / 9; /* Forces a landscape monitor shape */
        max-height: 85vh; /* Prevents it from getting too tall on weird monitors */
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: bold;
        color: white;
        border-radius: 12px;
        grid-column: 1; /* Keeps cross-fades stacking perfectly */
        grid-row: 1;
    }

    .viz-1 { background-color: #3498db; }
    .viz-2 { background-color: #e74c3c; }
    .viz-3 { background-color: #9b59b6; }
    .viz-4 { background-color: #f1c40f; color: #333; }
    .title-stage { background-color: #2c3e50; }
</style>
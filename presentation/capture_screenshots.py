"""
Capture screenshots of each step in the live site for use in the PPTX.

Saves to: presentation/assets/screenshots/step{N}_{name}.png
"""

from __future__ import annotations
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page

LIVE_URL = "https://57777-bit.github.io/5609finalProject/"
OUT_DIR = Path(__file__).resolve().parent / "assets" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# (step_index, filename, extra_setup_fn_name)
STEPS = [
    (0, "step0_scrollymap"),
    (1, "step1_scatter"),
    (2, "step2_changemap"),
    (3, "step3_schoolfunding"),
    (4, "step4_gatsby"),
    (5, "step5_dumbbell"),
    (6, "step6_league"),
    (7, "step7_3d"),
]


def wait_for_charts(page: Page, ms: int = 2500):
    page.wait_for_timeout(ms)


def scroll_to_step(page: Page, step_idx: int):
    page.evaluate(f"""(idx) => {{
        const steps = [...document.querySelectorAll('[data-step]')];
        if (!steps[idx]) return;
        const y = steps[idx].getBoundingClientRect().top + window.scrollY + 150;
        window.scrollTo({{ top: y, behavior: 'instant' }});
    }}""", step_idx)


def click_play_if_present(page: Page):
    """Click any Play button visible in the chart box."""
    page.evaluate("""() => {
        const btn = document.querySelector('.chart-box button, .canvas-wrap button');
        if (btn && /play|start/i.test(btn.textContent + (btn.getAttribute('aria-label') || ''))) {
            btn.click();
        }
    }""")


def crop_chart_box(page: Page, out_path: Path):
    """Screenshot just the chart-box (right panel)."""
    box = page.query_selector(".chart-box, .right-panel, .sticky-chart")
    if box:
        box.screenshot(path=str(out_path))
        return True
    # Fallback: right half of the viewport
    vp = page.viewport_size
    w, h = vp["width"], vp["height"]
    page.screenshot(
        path=str(out_path),
        clip={"x": w // 2, "y": 0, "width": w // 2, "height": h},
    )
    return False


def main():
    already = {f.name for f in OUT_DIR.glob("*.png")}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        page = browser.new_page(viewport={"width": 1600, "height": 900})

        print(f"Loading {LIVE_URL} …")
        page.goto(LIVE_URL, wait_until="networkidle", timeout=30_000)
        wait_for_charts(page, 3000)

        for step_idx, base_name in STEPS:
            fname = f"{base_name}.png"
            out_path = OUT_DIR / fname

            if fname in already:
                print(f"  skip  {fname}  (already exists)")
                continue

            print(f"  step {step_idx}  →  {fname}")
            scroll_to_step(page, step_idx)
            wait_for_charts(page, 2200)

            if step_idx == 0:
                click_play_if_present(page)
                wait_for_charts(page, 3500)

            if step_idx == 6:
                # Wait for the morph animation to complete (~1.5 s)
                wait_for_charts(page, 1800)

            if step_idx == 7:
                # deck.gl canvas — needs longer for WebGL to render after scroll
                wait_for_charts(page, 3000)

            crop_chart_box(page, out_path)
            size_kb = out_path.stat().st_size // 1024
            print(f"          saved  {size_kb} KB")

        browser.close()

    print("\nDone.  Files in", OUT_DIR)
    for p in sorted(OUT_DIR.glob("*.png")):
        print(f"  {p.name}  ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

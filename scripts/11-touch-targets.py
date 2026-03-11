#!/usr/bin/env python3
"""11-touch-targets.py — Mesure les tailles réelles des cibles tactiles en viewport mobile.

Utilise Playwright async pour ouvrir chaque page en viewport mobile,
collecter les éléments interactifs et mesurer leurs dimensions.

Usage : python3 scripts/11-touch-targets.py
Inputs : .audit/page-map.json, .audit/.env
Output : .audit/touch-targets/touch-{page-id}.json
"""

import asyncio
import json
import re
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.lib.file_utils import read_json, write_json, ensure_dir
from scripts.lib.progress import log_phase, log_step, log_success, log_error, log_skip
from scripts.lib.auth import load_env, get_auth_config

AUDIT_DIR = ".audit"
PAGE_MAP_PATH = os.path.join(AUDIT_DIR, "page-map.json")
OUTPUT_DIR = os.path.join(AUDIT_DIR, "touch-targets")
ERRORS_PATH = os.path.join(AUDIT_DIR, "script-errors.json")

INTERACTIVE_SELECTOR = (
    "a, button, input, select, textarea, "
    "[role='button'], [role='link'], [tabindex]"
)

# JS to collect interactive elements and their bounding rects
COLLECT_TARGETS_JS = """
() => {
    const selector = "a, button, input, select, textarea, " +
        "[role='button'], [role='link'], [tabindex]";
    const elements = Array.from(document.querySelectorAll(selector));
    return elements.map((el, idx) => {
        const rect = el.getBoundingClientRect();
        // Build a simple CSS selector
        let sel = el.tagName.toLowerCase();
        if (el.id) sel += '#' + el.id;
        else if (el.className && typeof el.className === 'string') {
            const cls = el.className.trim().split(/\\s+/).slice(0, 2).join('.');
            if (cls) sel += '.' + cls;
        }
        return {
            id: 'target-' + idx,
            selector: sel,
            tag: el.tagName.toLowerCase(),
            visible_text: (el.innerText || el.value || el.getAttribute('aria-label') || '').substring(0, 80),
            position: { x: rect.x, y: rect.y },
            width_px: rect.width,
            height_px: rect.height,
        };
    }).filter(t => t.width_px > 0 && t.height_px > 0);
}
"""


def compute_spacing(targets):
    """Compute spacing to nearest target for each target (edge-to-edge distance)."""
    n = len(targets)
    for i in range(n):
        min_dist = None
        ti = targets[i]
        xi, yi, wi, hi = ti["position"]["x"], ti["position"]["y"], ti["width_px"], ti["height_px"]
        for j in range(n):
            if i == j:
                continue
            tj = targets[j]
            xj, yj, wj, hj = tj["position"]["x"], tj["position"]["y"], tj["width_px"], tj["height_px"]

            # Edge-to-edge distance (axis-aligned)
            dx = max(0, max(xj - (xi + wi), xi - (xj + wj)))
            dy = max(0, max(yj - (yi + hi), yi - (yj + hj)))
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if min_dist is None or dist < min_dist:
                min_dist = dist
        ti["spacing_to_nearest_target_px"] = round(min_dist, 1) if min_dist is not None else None
    return targets


def build_summary(targets, threshold):
    """Build the summary object."""
    below = [t for t in targets if not t["passes_threshold"]]
    crowded = [t for t in targets if t.get("spacing_to_nearest_target_px") is not None and t["spacing_to_nearest_target_px"] < 8]
    total = len(targets)

    smallest = None
    if targets:
        smallest_t = min(targets, key=lambda t: min(t["width_px"], t["height_px"]))
        smallest = {
            "selector": smallest_t["selector"],
            "width_px": smallest_t["width_px"],
            "height_px": smallest_t["height_px"],
        }

    return {
        "total_targets": total,
        "below_threshold": len(below),
        "below_threshold_pct": round(len(below) / total * 100, 1) if total > 0 else 0,
        "smallest_target": smallest,
        "crowded_targets_count": len(crowded),
    }


def log_script_error(errors, script, page_id, message):
    """Append error to the shared script-errors list."""
    errors.append({
        "script": script,
        "page_id": page_id,
        "error": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def measure_page(browser, page_info, auth_config, env, errors):
    """Measure touch targets for a single page."""
    page_id = page_info["id"]
    output_path = os.path.join(OUTPUT_DIR, f"touch-{page_id}.json")

    # Idempotent: skip if output exists
    if os.path.exists(output_path):
        log_skip(f"touch-{page_id}.json")
        return

    mobile_width = int(env.get("SCREENSHOT_MOBILE_WIDTH", "375"))
    mobile_height = 812
    threshold = int(env.get("TOUCH_TARGET_THRESHOLD_PX", "44"))
    timeout = auth_config["playwright_timeout_ms"]

    url = page_info.get("url_or_path", "")
    if not url.startswith("http"):
        base = auth_config["base_url"].rstrip("/")
        url = base + ("" if url.startswith("/") else "/") + url

    # Skip parameterized routes
    if page_info.get("parameterized"):
        log_skip(f"{page_id} — route paramétrée, skip")
        return

    context = await browser.new_context(viewport={"width": mobile_width, "height": mobile_height})
    page = await context.new_page()
    try:
        log_step(f"Mesure touch targets : {page_id} → {url}")
        await page.goto(url, wait_until="networkidle", timeout=timeout)

        # Collect interactive elements
        targets = await page.evaluate(COLLECT_TARGETS_JS)

        # Mark threshold pass/fail
        for t in targets:
            t["passes_threshold"] = (t["width_px"] >= threshold and t["height_px"] >= threshold)

        # Compute spacing
        targets = compute_spacing(targets)

        summary = build_summary(targets, threshold)

        result = {
            "page_id": page_id,
            "url": url,
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "viewport_mobile": {"width": mobile_width, "height": mobile_height},
            "threshold_px": threshold,
            "targets": targets,
            "summary": summary,
        }
        write_json(output_path, result)
        log_success(f"touch-{page_id}.json — {summary['total_targets']} cibles, {summary['below_threshold']} < {threshold}px")

    except Exception as e:
        msg = str(e)
        log_error(f"{page_id} — {msg}")
        log_script_error(errors, "11-touch-targets.py", page_id, msg)
    finally:
        await page.close()
        await context.close()


async def main():
    log_phase("2+", "Touch Targets Audit",
              inputs=[PAGE_MAP_PATH, ".audit/.env"],
              outputs=[OUTPUT_DIR])

    page_map = read_json(PAGE_MAP_PATH)
    if not page_map:
        log_error(f"{PAGE_MAP_PATH} introuvable — lancez d'abord 03-build-page-map.py")
        sys.exit(1)

    env = load_env()
    auth_config = get_auth_config()
    ensure_dir(OUTPUT_DIR)

    # Load existing errors
    errors = read_json(ERRORS_PATH) or []

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log_error("playwright non installé — pip3 install playwright && playwright install chromium")
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for page_info in page_map.get("pages", []):
            await measure_page(browser, page_info, auth_config, env, errors)

        await browser.close()

    # Save errors
    if errors:
        write_json(ERRORS_PATH, errors)

    log_success("Audit touch targets terminé")


if __name__ == "__main__":
    asyncio.run(main())

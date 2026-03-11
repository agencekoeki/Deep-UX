#!/usr/bin/env python3
"""12-nav-keyboard.py — Simule la navigation clavier et audite le focus.

Utilise Playwright async pour naviguer avec Tab et analyser le focus
de chaque élément, détecter les pièges de focus et les éléments inaccessibles.

Usage : python3 scripts/12-nav-keyboard.py
Inputs : .audit/page-map.json, .audit/.env, .audit/dom/dom-{page-id}.json (optionnel)
Output : .audit/keyboard-nav/keyboard-{page-id}.json
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
DOM_DIR = os.path.join(AUDIT_DIR, "dom")
OUTPUT_DIR = os.path.join(AUDIT_DIR, "keyboard-nav")
ERRORS_PATH = os.path.join(AUDIT_DIR, "script-errors.json")

MAX_TABS = 200

# JS to get info about the currently focused element
GET_ACTIVE_ELEMENT_JS = """
() => {
    const el = document.activeElement;
    if (!el || el === document.body || el === document.documentElement) {
        return null;
    }
    const rect = el.getBoundingClientRect();
    const style = window.getComputedStyle(el);

    // Build a CSS selector
    let sel = el.tagName.toLowerCase();
    if (el.id) sel += '#' + el.id;
    else if (el.className && typeof el.className === 'string') {
        const cls = el.className.trim().split(/\\s+/).slice(0, 2).join('.');
        if (cls) sel += '.' + cls;
    }

    const outline = style.outline || '';
    const outlineWidth = style.outlineWidth || '0px';
    const outlineStyle = style.outlineStyle || 'none';
    const boxShadow = style.boxShadow || 'none';

    const hasOutline = outlineStyle !== 'none' && outlineWidth !== '0px';
    const hasBoxShadow = boxShadow !== 'none' && boxShadow !== '';
    const hasFocusIndicator = hasOutline || hasBoxShadow;

    let focusStyle = null;
    if (hasOutline) {
        focusStyle = 'outline: ' + outline;
    } else if (hasBoxShadow) {
        focusStyle = 'box-shadow: ' + boxShadow;
    }

    return {
        selector: sel,
        tag: el.tagName.toLowerCase(),
        visible_text: (el.innerText || el.value || el.getAttribute('aria-label') || '').substring(0, 80),
        has_focus_indicator: hasFocusIndicator,
        focus_indicator_style: focusStyle,
        position: { x: rect.x, y: rect.y },
    };
}
"""

# JS to count elements with positive tabindex
GET_POSITIVE_TABINDEX_JS = """
() => {
    const els = document.querySelectorAll('[tabindex]');
    let count = 0;
    for (const el of els) {
        if (el.tabIndex > 0) count++;
    }
    return count;
}
"""

# JS to get all interactive elements on the page (for cross-referencing)
GET_INTERACTIVE_ELEMENTS_JS = """
() => {
    const selector = "a[href], button, input, select, textarea, " +
        "[role='button'], [role='link'], [tabindex]:not([tabindex='-1'])";
    const elements = Array.from(document.querySelectorAll(selector));
    return elements.map(el => {
        let sel = el.tagName.toLowerCase();
        if (el.id) sel += '#' + el.id;
        else if (el.className && typeof el.className === 'string') {
            const cls = el.className.trim().split(/\\s+/).slice(0, 2).join('.');
            if (cls) sel += '.' + cls;
        }
        return sel;
    });
}
"""


def detect_focus_traps(tab_sequence):
    """Detect focus traps: 10+ consecutive tabs cycling through the same small set of elements."""
    traps = []
    if len(tab_sequence) < 10:
        return traps

    window_size = 10
    for i in range(len(tab_sequence) - window_size + 1):
        window = tab_sequence[i:i + window_size]
        selectors_in_window = [item["selector"] for item in window]
        unique_in_window = set(selectors_in_window)

        # If 10 consecutive tabs cycle through <= 3 unique elements, it's a trap
        if len(unique_in_window) <= 3:
            trap_sel = list(unique_in_window)[0]
            # Avoid duplicate trap reports
            if not any(t["selector"] == trap_sel for t in traps):
                traps.append({
                    "selector": trap_sel,
                    "description": f"Focus piégé : {len(unique_in_window)} élément(s) en boucle sur {window_size} tabs consécutifs",
                })
            break  # One trap per page is enough to flag

    return traps


def detect_illogical_order(tab_sequence):
    """Detect illogical tab order: large backward jumps in Y position."""
    issues = []
    for i in range(1, len(tab_sequence)):
        prev = tab_sequence[i - 1]
        curr = tab_sequence[i]
        prev_y = prev.get("position", {}).get("y", 0)
        curr_y = curr.get("position", {}).get("y", 0)

        # A backward jump of more than 200px suggests illogical order
        if prev_y - curr_y > 200:
            issues.append({
                "from_selector": prev["selector"],
                "to_selector": curr["selector"],
                "description": f"Saut arrière de {int(prev_y - curr_y)}px en Y (de y={int(prev_y)} à y={int(curr_y)})",
            })

    return issues


def find_unreachable(all_interactive, reached_selectors):
    """Find interactive elements that were never reached via Tab."""
    reached = set(reached_selectors)
    unreachable = []
    for sel in all_interactive:
        if sel not in reached:
            unreachable.append(sel)
    return unreachable


def compute_keyboard_score(traps, missing_indicators, illogical_order, unreachable):
    """Compute keyboard accessibility score (100 base)."""
    score = 100
    score -= len(traps) * 10
    score -= len(missing_indicators) * 2
    score -= len(illogical_order) * 5
    score -= len(unreachable) * 5
    return max(0, score)


def log_script_error(errors, script, page_id, message):
    """Append error to the shared script-errors list."""
    errors.append({
        "script": script,
        "page_id": page_id,
        "error": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


async def audit_page(browser, page_info, auth_config, env, errors):
    """Audit keyboard navigation for a single page."""
    page_id = page_info["id"]
    output_path = os.path.join(OUTPUT_DIR, f"keyboard-{page_id}.json")

    # Idempotent: skip if output exists
    if os.path.exists(output_path):
        log_skip(f"keyboard-{page_id}.json")
        return

    timeout = auth_config["playwright_timeout_ms"]

    url = page_info.get("url_or_path", "")
    if not url.startswith("http"):
        base = auth_config["base_url"].rstrip("/")
        url = base + ("" if url.startswith("/") else "/") + url

    if page_info.get("parameterized"):
        log_skip(f"{page_id} — route paramétrée, skip")
        return

    context = await browser.new_context(
        viewport={"width": auth_config["viewport_width"], "height": auth_config["viewport_height"]}
    )
    page = await context.new_page()
    try:
        log_step(f"Audit clavier : {page_id} → {url}")
        await page.goto(url, wait_until="networkidle", timeout=timeout)

        # Click body to ensure focus starts from top of page
        await page.evaluate("() => document.body.focus()")

        tab_sequence = []
        seen_selectors = set()

        for tab_idx in range(MAX_TABS):
            await page.keyboard.press("Tab")
            # Small delay to let focus settle
            await page.wait_for_timeout(50)

            info = await page.evaluate(GET_ACTIVE_ELEMENT_JS)
            if info is None:
                # Focus went to body or document — likely end of focusable elements
                continue

            entry = {
                "order": tab_idx + 1,
                "selector": info["selector"],
                "tag": info["tag"],
                "visible_text": info["visible_text"],
                "has_focus_indicator": info["has_focus_indicator"],
                "focus_indicator_style": info["focus_indicator_style"],
                "position": info["position"],
            }
            tab_sequence.append(entry)
            seen_selectors.add(info["selector"])

            # Early termination: if we've looped back to the first element after covering many
            if len(tab_sequence) > 5 and info["selector"] == tab_sequence[0]["selector"]:
                # Check if we've seen a reasonable number of elements
                if len(seen_selectors) > 2:
                    break

        # Detect positive tabindex
        positive_tabindex_count = await page.evaluate(GET_POSITIVE_TABINDEX_JS)

        # Get all interactive elements on page for cross-reference
        all_interactive = await page.evaluate(GET_INTERACTIVE_ELEMENTS_JS)

        # Also try to load DOM inventory for deeper cross-reference
        dom_path = os.path.join(DOM_DIR, f"dom-{page_id}.json")
        dom_data = read_json(dom_path)
        if dom_data and "interactive_elements" in dom_data:
            for el in dom_data["interactive_elements"]:
                sel = el.get("selector", "")
                if sel and sel not in all_interactive:
                    all_interactive.append(sel)

        # Analysis
        reached_selectors = [entry["selector"] for entry in tab_sequence]

        traps = detect_focus_traps(tab_sequence)
        illogical = detect_illogical_order(tab_sequence)
        unreachable = find_unreachable(all_interactive, set(reached_selectors))

        missing_indicators = [
            {"selector": e["selector"], "tag": e["tag"], "visible_text": e["visible_text"]}
            for e in tab_sequence if not e["has_focus_indicator"]
        ]
        # Deduplicate missing indicators by selector
        seen_missing = set()
        deduped_missing = []
        for m in missing_indicators:
            if m["selector"] not in seen_missing:
                seen_missing.add(m["selector"])
                deduped_missing.append(m)
        missing_indicators = deduped_missing

        score = compute_keyboard_score(traps, missing_indicators, illogical, unreachable)

        # Deduplicate tab_sequence for summary count
        unique_focusable = set(e["selector"] for e in tab_sequence)

        result = {
            "page_id": page_id,
            "url": url,
            "audited_at": datetime.now(timezone.utc).isoformat(),
            "tab_sequence": tab_sequence,
            "issues": {
                "focus_traps": traps,
                "missing_focus_indicators": missing_indicators,
                "illogical_tab_order": illogical,
                "positive_tabindex_count": positive_tabindex_count,
                "interactive_unreachable": unreachable,
            },
            "summary": {
                "total_focusable": len(unique_focusable),
                "without_focus_indicator": len(missing_indicators),
                "without_focus_indicator_pct": round(
                    len(missing_indicators) / len(unique_focusable) * 100, 1
                ) if unique_focusable else 0,
                "focus_traps_count": len(traps),
                "keyboard_score": score,
            },
        }

        write_json(output_path, result)
        log_success(
            f"keyboard-{page_id}.json — {len(unique_focusable)} focusables, "
            f"score={score}/100"
        )

    except Exception as e:
        msg = str(e)
        log_error(f"{page_id} — {msg}")
        log_script_error(errors, "12-nav-keyboard.py", page_id, msg)
    finally:
        await page.close()
        await context.close()


async def main():
    log_phase("2+", "Keyboard Navigation Audit",
              inputs=[PAGE_MAP_PATH, ".audit/.env"],
              outputs=[OUTPUT_DIR])

    page_map = read_json(PAGE_MAP_PATH)
    if not page_map:
        log_error(f"{PAGE_MAP_PATH} introuvable — lancez d'abord 03-build-page-map.py")
        sys.exit(1)

    env = load_env()
    auth_config = get_auth_config()
    ensure_dir(OUTPUT_DIR)

    errors = read_json(ERRORS_PATH) or []

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log_error("playwright non installé — pip3 install playwright && playwright install chromium")
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for page_info in page_map.get("pages", []):
            await audit_page(browser, page_info, auth_config, env, errors)

        await browser.close()

    if errors:
        write_json(ERRORS_PATH, errors)

    log_success("Audit navigation clavier terminé")


if __name__ == "__main__":
    asyncio.run(main())

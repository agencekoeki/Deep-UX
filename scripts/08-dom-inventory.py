#!/usr/bin/env python3
"""08-dom-inventory.py — Inventories all interactive DOM elements with positions.

Reads .audit/.env for credentials and base URL.
Reads .audit/page-map.json for the list of pages.
Outputs .audit/dom/dom-{page-id}.json per page.

Limitations:
- iframes are not inventoried (cross-origin restrictions)
- Shadow DOM is not traversed (requires specialized access)

Usage : python3 scripts/08-dom-inventory.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.lib.file_utils import read_json, write_json, ensure_dir
from scripts.lib.progress import log_phase, log_step, log_success, log_error, log_skip
from scripts.lib.auth import load_env, get_auth_config, load_auth_state, save_auth_state

AUDIT_DIR = ".audit"
PAGE_MAP_PATH = os.path.join(AUDIT_DIR, "page-map.json")
OUTPUT_DIR = os.path.join(AUDIT_DIR, "dom")
ERRORS_PATH = os.path.join(AUDIT_DIR, "script-errors.json")

# Selectors for interactive elements
INTERACTIVE_SELECTOR = "a, button, input, select, textarea, [role='button'], [role='link'], [tabindex]"

# JavaScript to collect all interactive elements
COLLECT_ELEMENTS_JS = """
(viewportHeight) => {
    const selector = "a, button, input, select, textarea, [role='button'], [role='link'], [tabindex]";
    const elements = document.querySelectorAll(selector);
    const results = [];
    let idx = 0;

    for (const el of elements) {
        idx++;
        const rect = el.getBoundingClientRect();
        const tag = el.tagName.toLowerCase();
        const inputType = el.getAttribute('type') || '';
        const role = el.getAttribute('role') || null;

        // Determine element type
        let type = 'other_interactive';
        if (tag === 'button' || role === 'button') {
            type = 'button';
        } else if (tag === 'a' || role === 'link') {
            type = 'link';
        } else if (tag === 'input') {
            if (inputType === 'checkbox') type = 'input_checkbox';
            else if (inputType === 'radio') type = 'input_radio';
            else if (inputType === 'file') type = 'input_file';
            else type = 'input_text';
        } else if (tag === 'select') {
            type = 'input_select';
        } else if (tag === 'textarea') {
            type = 'textarea';
        }

        // Build a unique CSS selector
        let selectorPath = tag;
        if (el.id) {
            selectorPath = `${tag}#${CSS.escape(el.id)}`;
        } else if (el.className && typeof el.className === 'string' && el.className.trim()) {
            const classes = el.className.trim().split(/\\s+/).slice(0, 3).map(c => '.' + CSS.escape(c)).join('');
            selectorPath = `${tag}${classes}`;
        }

        // Get visible text (trimmed, max 200 chars)
        let visibleText = '';
        if (tag === 'input' || tag === 'textarea') {
            visibleText = el.placeholder || el.value || '';
        } else {
            visibleText = (el.innerText || el.textContent || '').trim();
        }
        visibleText = visibleText.substring(0, 200).replace(/\\s+/g, ' ').trim();

        const ariaLabel = el.getAttribute('aria-label') || null;
        const ariaRole = el.getAttribute('role') || null;
        const disabled = el.disabled === true || el.getAttribute('aria-disabled') === 'true';
        const tabIdx = el.hasAttribute('tabindex') ? parseInt(el.getAttribute('tabindex'), 10) : null;
        const inViewport = rect.top >= 0 && rect.top < viewportHeight && rect.width > 0 && rect.height > 0;

        results.push({
            id: `elem-${String(idx).padStart(3, '0')}`,
            tag: tag,
            type: type,
            selector: selectorPath,
            position: {
                x: Math.round(rect.x * 100) / 100,
                y: Math.round(rect.y * 100) / 100,
                width: Math.round(rect.width * 100) / 100,
                height: Math.round(rect.height * 100) / 100
            },
            visible_text: visibleText,
            aria_label: ariaLabel,
            aria_role: ariaRole,
            disabled: disabled,
            in_viewport: inViewport,
            tab_index: isNaN(tabIdx) ? null : tabIdx
        });
    }

    return results;
}
"""


async def perform_form_login(page, auth_config):
    """Effectue un login via formulaire (async)."""
    login_url = auth_config["base_url"].rstrip("/") + auth_config["login_url"]
    log_step(f"Login via formulaire : {login_url}")

    timeout = auth_config["playwright_timeout_ms"]
    await page.goto(login_url, wait_until="networkidle", timeout=timeout)

    username_selectors = [
        'input[type="email"]', 'input[name="email"]', 'input[name="username"]',
        'input[id="email"]', 'input[id="username"]', 'input[type="text"]',
    ]
    for selector in username_selectors:
        el = await page.query_selector(selector)
        if el:
            await el.fill(auth_config["username"])
            break

    password_selectors = [
        'input[type="password"]', 'input[name="password"]', 'input[id="password"]',
    ]
    for selector in password_selectors:
        el = await page.query_selector(selector)
        if el:
            await el.fill(auth_config["password"])
            break

    submit_selectors = [
        'button[type="submit"]', 'input[type="submit"]',
        'button:has-text("Login")', 'button:has-text("Sign in")',
        'button:has-text("Connexion")', 'button:has-text("Se connecter")',
    ]
    for selector in submit_selectors:
        el = await page.query_selector(selector)
        if el:
            await el.click()
            break

    try:
        await page.wait_for_url(f"**{auth_config['success_url']}**", timeout=15000)
        log_success("Login réussi")
    except Exception:
        log_error("Login — redirection non détectée, tentative de continuer")


async def inventory_page(context, page_info, auth_config, errors):
    """Inventories all interactive elements on a single page."""
    page_id = page_info["id"]
    output_path = os.path.join(OUTPUT_DIR, f"dom-{page_id}.json")

    # Idempotent: skip if output already exists
    if os.path.exists(output_path):
        log_skip(f"{page_id} — DOM déjà inventorié")
        return

    # Skip parameterized routes
    if page_info.get("parameterized"):
        msg = f"Route paramétrée skippée : {page_info['url_or_path']}"
        log_error(f"{page_id} — {msg}")
        errors.append({
            "script": "08-dom-inventory",
            "page_id": page_id,
            "url": page_info["url_or_path"],
            "error": msg,
            "error_type": "parameterized_route",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return

    url = page_info["url_or_path"]
    if not url.startswith("http"):
        url = auth_config["base_url"].rstrip("/") + ("" if url.startswith("/") else "/") + url

    page = await context.new_page()
    try:
        log_step(f"DOM inventory : {page_id} → {url}")
        timeout = auth_config["playwright_timeout_ms"]
        await page.goto(url, wait_until="networkidle", timeout=timeout)

        viewport_height = auth_config["viewport_height"]
        elements = await page.evaluate(COLLECT_ELEMENTS_JS, viewport_height)

        # Build summary
        buttons_count = sum(1 for e in elements if e["type"] == "button")
        links_count = sum(1 for e in elements if e["type"] == "link")
        inputs_count = sum(1 for e in elements if e["type"].startswith("input_") or e["type"] == "textarea")
        above_fold_count = sum(1 for e in elements if e["in_viewport"])

        result = {
            "page_id": page_id,
            "url": url,
            "inventoried_at": datetime.now(timezone.utc).isoformat(),
            "viewport": {
                "width": auth_config["viewport_width"],
                "height": viewport_height,
            },
            "elements": elements,
            "summary": {
                "total_interactive": len(elements),
                "buttons_count": buttons_count,
                "links_count": links_count,
                "inputs_count": inputs_count,
                "above_fold_count": above_fold_count,
            },
            "_limitations": [
                "iframes not inventoried (cross-origin restrictions)",
                "Shadow DOM not traversed (requires specialized access)"
            ],
        }

        write_json(output_path, result)
        log_success(f"{page_id} — {len(elements)} éléments interactifs ({buttons_count} boutons, {links_count} liens, {inputs_count} inputs)")

    except Exception as e:
        error_msg = str(e)
        log_error(f"{page_id} — {error_msg}")
        errors.append({
            "script": "08-dom-inventory",
            "page_id": page_id,
            "url": url,
            "error": error_msg,
            "error_type": "inventory_failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    finally:
        await page.close()


async def main():
    log_phase(2, "DOM Inventory", inputs=[PAGE_MAP_PATH, ".audit/.env"], outputs=[OUTPUT_DIR])

    page_map = read_json(PAGE_MAP_PATH)
    if not page_map:
        log_error(f"{PAGE_MAP_PATH} introuvable — lancez d'abord 03-build-page-map.py")
        sys.exit(1)

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
        context_options = {
            "viewport": {
                "width": auth_config["viewport_width"],
                "height": auth_config["viewport_height"],
            }
        }

        # Handle authentication
        if auth_config["auth_type"] == "sso":
            auth_state = load_auth_state()
            if auth_state:
                context_options["storage_state"] = auth_state
                log_success("Auth SSO — storage state chargé")
            else:
                log_error("Auth SSO — auth-state.json introuvable. Lancez 06-export-session-helper.py")
                await browser.close()
                sys.exit(1)

        context = await browser.new_context(**context_options)

        # Form login
        if auth_config["auth_type"] == "form":
            login_page = await context.new_page()
            await perform_form_login(login_page, auth_config)
            state = await context.storage_state()
            save_auth_state(state)
            await login_page.close()

        # Filter excluded URLs
        exclude_urls = auth_config["exclude_urls"]
        pages_to_scan = []
        for page_info in page_map["pages"]:
            url_or_path = page_info["url_or_path"]
            excluded = False
            for pattern in exclude_urls:
                if url_or_path == pattern or url_or_path.startswith(pattern.rstrip("/") + "/"):
                    excluded = True
                    break
            if excluded:
                log_skip(f"{page_info['id']} — exclu par EXCLUDE_URLS ({url_or_path})")
            else:
                pages_to_scan.append(page_info)

        # Inventory each page
        for page_info in pages_to_scan:
            await inventory_page(context, page_info, auth_config, errors)

        await context.close()
        await browser.close()

    # Save errors
    if errors:
        write_json(ERRORS_PATH, errors)
        log_error(f"{len(errors)} erreur(s) enregistrée(s) dans {ERRORS_PATH}")

    log_success("DOM inventory terminé")


if __name__ == "__main__":
    asyncio.run(main())

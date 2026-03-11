#!/usr/bin/env python3
"""07-a11y-scan.py — Runs axe-core accessibility scan on each page via Playwright.

Reads .audit/.env for credentials and base URL.
Reads .audit/page-map.json for the list of pages.
Outputs .audit/a11y/a11y-{page-id}.json per page.

Usage : python3 scripts/07-a11y-scan.py
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
OUTPUT_DIR = os.path.join(AUDIT_DIR, "a11y")
ERRORS_PATH = os.path.join(AUDIT_DIR, "script-errors.json")

AXE_CDN_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js"
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21aa", "best-practice"]


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


async def scan_page(context, page_info, auth_config, errors):
    """Injects axe-core and runs accessibility scan on a single page."""
    page_id = page_info["id"]
    output_path = os.path.join(OUTPUT_DIR, f"a11y-{page_id}.json")

    # Idempotent: skip if output already exists
    if os.path.exists(output_path):
        log_skip(f"{page_id} — a11y déjà scanné")
        return

    # Skip parameterized routes
    if page_info.get("parameterized"):
        msg = f"Route paramétrée skippée : {page_info['url_or_path']}"
        log_error(f"{page_id} — {msg}")
        errors.append({
            "script": "07-a11y-scan",
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
        log_step(f"A11y scan : {page_id} → {url}")
        timeout = auth_config["playwright_timeout_ms"]
        await page.goto(url, wait_until="networkidle", timeout=timeout)

        # Inject axe-core via CDN
        await page.add_script_tag(url=AXE_CDN_URL)
        # Wait for axe to be available
        await page.wait_for_function("typeof window.axe !== 'undefined'", timeout=15000)

        # Run axe with specified tags
        axe_results = await page.evaluate("""
            async (tags) => {
                const results = await axe.run(document, {
                    runOnly: { type: 'tag', values: tags }
                });
                return {
                    violations: results.violations,
                    passes_count: results.passes.length,
                    incomplete: results.incomplete,
                    testEngine: results.testEngine
                };
            }
        """, AXE_TAGS)

        # Process violations
        violations = []
        violations_by_impact = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}

        for v in axe_results["violations"]:
            impact = v.get("impact", "minor")
            if impact in violations_by_impact:
                violations_by_impact[impact] += 1

            nodes = []
            for node in v.get("nodes", []):
                node_data = {
                    "html": node.get("html", "")[:200],
                    "selector": ", ".join(node.get("target", [])) if node.get("target") else "",
                    "failure_summary": node.get("failureSummary", ""),
                }
                # Get bounding box for first node
                if node.get("target") and len(node["target"]) > 0:
                    try:
                        selector = node["target"][0]
                        position = await page.evaluate("""
                            (selector) => {
                                const el = document.querySelector(selector);
                                if (!el) return null;
                                const rect = el.getBoundingClientRect();
                                return {
                                    x: Math.round(rect.x),
                                    y: Math.round(rect.y),
                                    width: Math.round(rect.width),
                                    height: Math.round(rect.height)
                                };
                            }
                        """, selector)
                        if position:
                            node_data["position"] = position
                    except Exception:
                        pass
                nodes.append(node_data)

            wcag_criteria = []
            for tag in v.get("tags", []):
                wcag_criteria.append(tag)

            violations.append({
                "id": v.get("id", ""),
                "impact": impact,
                "description": v.get("description", ""),
                "help_url": v.get("helpUrl", ""),
                "wcag_criteria": wcag_criteria,
                "nodes": nodes,
            })

        # Process incomplete
        incomplete = []
        for inc in axe_results.get("incomplete", []):
            incomplete.append({
                "id": inc.get("id", ""),
                "description": inc.get("description", ""),
                "nodes_count": len(inc.get("nodes", [])),
            })

        engine_info = axe_results.get("testEngine", {})
        engine = f"{engine_info.get('name', 'axe-core')} {engine_info.get('version', '4.9.1')}"

        result = {
            "page_id": page_id,
            "url": url,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "engine": engine,
            "violations": violations,
            "passes_count": axe_results["passes_count"],
            "incomplete": incomplete,
            "violations_by_impact": violations_by_impact,
        }

        write_json(output_path, result)
        total_violations = len(violations)
        log_success(f"{page_id} — {total_violations} violation(s), {axe_results['passes_count']} passe(s)")

    except Exception as e:
        error_msg = str(e)
        log_error(f"{page_id} — {error_msg}")
        errors.append({
            "script": "07-a11y-scan",
            "page_id": page_id,
            "url": url,
            "error": error_msg,
            "error_type": "scan_failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    finally:
        await page.close()


async def main():
    log_phase(2, "A11y Scan (axe-core)", inputs=[PAGE_MAP_PATH, ".audit/.env"], outputs=[OUTPUT_DIR])

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

        # Scan each page
        for page_info in pages_to_scan:
            await scan_page(context, page_info, auth_config, errors)

        await context.close()
        await browser.close()

    # Save errors
    if errors:
        write_json(ERRORS_PATH, errors)
        log_error(f"{len(errors)} erreur(s) enregistrée(s) dans {ERRORS_PATH}")

    log_success("A11y scan terminé")


if __name__ == "__main__":
    asyncio.run(main())

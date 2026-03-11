#!/usr/bin/env python3
"""04-screenshot.py — Capture chaque page en pleine hauteur avec Playwright.

Lit .audit/.env pour les credentials et l'URL de base.
Lit .audit/page-map.json pour la liste des pages.
Met à jour page-map.json avec screenshot_path et timestamp.

Usage : python3 scripts/04-screenshot.py
"""

import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from file_utils import read_json, write_json, ensure_dir
from auth import load_env, get_auth_config, load_auth_state, save_auth_state
from progress import log_phase, log_step, log_success, log_error, log_skip

AUDIT_DIR = ".audit"
PAGE_MAP_PATH = os.path.join(AUDIT_DIR, "page-map.json")
SCREENSHOTS_DIR = os.path.join(AUDIT_DIR, "screenshots")
ERRORS_PATH = os.path.join(AUDIT_DIR, "screenshot-errors.json")


def perform_form_login(page, auth_config):
    """Effectue un login via formulaire."""
    login_url = auth_config["base_url"].rstrip("/") + auth_config["login_url"]
    log_step(f"Login via formulaire : {login_url}")

    page.goto(login_url, wait_until="networkidle", timeout=30000)

    # Find and fill username field
    username_selectors = [
        'input[type="email"]', 'input[name="email"]', 'input[name="username"]',
        'input[id="email"]', 'input[id="username"]', 'input[type="text"]',
    ]
    for selector in username_selectors:
        el = page.query_selector(selector)
        if el:
            el.fill(auth_config["username"])
            break

    # Find and fill password field
    password_selectors = [
        'input[type="password"]', 'input[name="password"]', 'input[id="password"]',
    ]
    for selector in password_selectors:
        el = page.query_selector(selector)
        if el:
            el.fill(auth_config["password"])
            break

    # Find and click submit
    submit_selectors = [
        'button[type="submit"]', 'input[type="submit"]',
        'button:has-text("Login")', 'button:has-text("Sign in")',
        'button:has-text("Connexion")', 'button:has-text("Se connecter")',
    ]
    for selector in submit_selectors:
        el = page.query_selector(selector)
        if el:
            el.click()
            break

    # Wait for redirect
    try:
        page.wait_for_url(f"**{auth_config['success_url']}**", timeout=15000)
        log_success("Login réussi")
    except Exception:
        log_error("Login — redirection non détectée, tentative de continuer")


def capture_page(browser_context, page_info, auth_config, errors):
    """Capture une page en pleine hauteur."""
    page_id = page_info["id"]
    screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{page_id}.png")

    # Skip if already captured
    if page_info.get("screenshot_path") and os.path.exists(page_info["screenshot_path"]):
        log_skip(f"{page_id} — déjà capturé")
        return page_info["screenshot_path"]

    url = page_info["url_or_path"]
    if not url.startswith("http"):
        url = auth_config["base_url"].rstrip("/") + ("" if url.startswith("/") else "/") + url

    page = browser_context.new_page()
    try:
        log_step(f"Capture : {page_id} → {url}")
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.screenshot(path=screenshot_path, full_page=True)
        log_success(f"{page_id} → {screenshot_path}")
        return screenshot_path
    except Exception as e:
        error_msg = str(e)
        log_error(f"{page_id} — {error_msg}")
        errors.append({
            "page_id": page_id,
            "url": url,
            "error": error_msg,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return None
    finally:
        page.close()


def main():
    log_phase(2, "Screenshots", inputs=[PAGE_MAP_PATH, ".audit/.env"], outputs=[SCREENSHOTS_DIR])

    page_map = read_json(PAGE_MAP_PATH)
    if not page_map:
        log_error(f"{PAGE_MAP_PATH} introuvable — lancez d'abord 03-build-page-map.py")
        sys.exit(1)

    auth_config = get_auth_config()
    ensure_dir(SCREENSHOTS_DIR)

    # Load existing errors
    errors = read_json(ERRORS_PATH) or []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log_error("playwright non installé — pip3 install playwright && playwright install chromium")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context_options = {
            "viewport": {
                "width": auth_config["viewport_width"],
                "height": auth_config["viewport_height"],
            }
        }

        # Handle authentication
        auth_state = None
        if auth_config["auth_type"] == "sso":
            auth_state = load_auth_state()
            if auth_state:
                context_options["storage_state"] = auth_state
                log_success("Auth SSO — storage state chargé")
            else:
                log_error("Auth SSO — auth-state.json introuvable. Lancez 06-export-session-helper.py")
                browser.close()
                sys.exit(1)

        context = browser.new_context(**context_options)

        # Form login
        if auth_config["auth_type"] == "form":
            login_page = context.new_page()
            perform_form_login(login_page, auth_config)
            # Save state for reuse
            state = context.storage_state()
            save_auth_state(state)
            login_page.close()

        # Capture all pages
        updated = False
        for page_info in page_map["pages"]:
            result = capture_page(context, page_info, auth_config, errors)
            if result:
                page_info["screenshot_path"] = result
                page_info["screenshot_at"] = datetime.now(timezone.utc).isoformat()
                updated = True
                # Save incrementally
                write_json(PAGE_MAP_PATH, page_map)

        context.close()
        browser.close()

    # Save errors
    if errors:
        write_json(ERRORS_PATH, errors)
        log_error(f"{len(errors)} erreur(s) enregistrée(s) dans {ERRORS_PATH}")

    log_success("Captures terminées")


if __name__ == "__main__":
    main()

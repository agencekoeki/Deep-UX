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
import time
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

    timeout = auth_config["playwright_timeout_ms"]
    page.goto(login_url, wait_until="networkidle", timeout=timeout)

    # Find and fill username field
    username_selectors = [
        'input[type="email"]', 'input[name="email"]', 'input[name="username"]',
        'input[id="email"]', 'input[id="username"]', 'input[type="text"]',
    ]
    username_found = False
    for selector in username_selectors:
        el = page.query_selector(selector)
        if el:
            el.fill(auth_config["username"])
            username_found = True
            break
    if not username_found:
        log_error("Login — aucun champ username/email trouvé sur la page")

    # Find and fill password field
    password_selectors = [
        'input[type="password"]', 'input[name="password"]', 'input[id="password"]',
    ]
    password_found = False
    for selector in password_selectors:
        el = page.query_selector(selector)
        if el:
            el.fill(auth_config["password"])
            password_found = True
            break
    if not password_found:
        log_error("Login — aucun champ password trouvé sur la page")

    # Find and click submit
    submit_selectors = [
        'button[type="submit"]', 'input[type="submit"]',
        'button:has-text("Login")', 'button:has-text("Sign in")',
        'button:has-text("Connexion")', 'button:has-text("Se connecter")',
    ]
    submit_found = False
    for selector in submit_selectors:
        el = page.query_selector(selector)
        if el:
            el.click()
            submit_found = True
            break
    if not submit_found:
        log_error("Login — aucun bouton submit trouvé sur la page")

    # Wait for redirect
    try:
        page.wait_for_url(f"**{auth_config['success_url']}**", timeout=15000)
        log_success("Login réussi")
    except Exception:
        log_error("Login — redirection non détectée, tentative de continuer")


def is_excluded(url_or_path, exclude_urls):
    """Vérifie si une URL est dans la liste d'exclusion."""
    for pattern in exclude_urls:
        # Match exact
        if url_or_path == pattern:
            return True
        # Match début de segment : /api exclut /api/users mais pas /api-documentation
        if url_or_path.startswith(pattern.rstrip('/') + '/'):
            return True
    return False


def capture_page(browser_context, page_info, auth_config, errors, suffix=""):
    """Capture une page en pleine hauteur.

    Args:
        suffix: suffixe ajouté au nom du fichier screenshot (ex: "-mobile")
    """
    page_id = page_info["id"]
    screenshot_name = f"{page_id}{suffix}.png"
    screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_name)
    timeout = auth_config["playwright_timeout_ms"]
    delay_ms = auth_config["screenshot_delay_ms"]

    # Skip if already captured
    if not suffix and page_info.get("screenshot_path") and os.path.exists(page_info["screenshot_path"]):
        log_skip(f"{page_id}{suffix} — déjà capturé")
        return page_info["screenshot_path"]
    if suffix and os.path.exists(screenshot_path):
        log_skip(f"{page_id}{suffix} — déjà capturé")
        return screenshot_path

    # Skip parameterized routes
    if page_info.get("parameterized"):
        msg = f"Route paramétrée skippée (pas de valeur de test) : {page_info['url_or_path']}"
        log_error(f"{page_id}{suffix} — {msg}")
        errors.append({
            "page_id": page_id,
            "url": page_info["url_or_path"],
            "error": msg,
            "error_type": "parameterized_route",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return None

    url = page_info["url_or_path"]
    if not url.startswith("http"):
        url = auth_config["base_url"].rstrip("/") + ("" if url.startswith("/") else "/") + url

    page = browser_context.new_page()
    try:
        log_step(f"Capture : {page_id}{suffix} → {url}")
        page.goto(url, wait_until="networkidle", timeout=timeout)
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
        page.screenshot(path=screenshot_path, full_page=True)
        log_success(f"{page_id}{suffix} → {screenshot_path}")
        return screenshot_path
    except Exception as e:
        error_msg = str(e)
        log_error(f"{page_id}{suffix} — {error_msg}")
        errors.append({
            "page_id": page_id,
            "url": url,
            "error": error_msg,
            "error_type": "capture_failed",
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

        # Filter excluded URLs
        exclude_urls = auth_config["exclude_urls"]
        pages_to_capture = []
        for page_info in page_map["pages"]:
            if is_excluded(page_info["url_or_path"], exclude_urls):
                log_skip(f"{page_info['id']} — exclu par EXCLUDE_URLS ({page_info['url_or_path']})")
            else:
                pages_to_capture.append(page_info)

        if exclude_urls:
            excluded_count = len(page_map["pages"]) - len(pages_to_capture)
            log_step(f"{excluded_count} page(s) exclue(s) par EXCLUDE_URLS")

        # Desktop pass
        for page_info in pages_to_capture:
            result = capture_page(context, page_info, auth_config, errors)
            if result:
                page_info["screenshot_path"] = result
                page_info["screenshot_at"] = datetime.now(timezone.utc).isoformat()
                # Save incrementally
                write_json(PAGE_MAP_PATH, page_map)

        context.close()

        # Mobile pass
        if auth_config["screenshot_mobile"]:
            mobile_width = auth_config["screenshot_mobile_width"]
            log_step(f"Passe mobile ({mobile_width}px)...")
            mobile_context_options = {
                "viewport": {"width": mobile_width, "height": 812}
            }
            if auth_config["auth_type"] == "sso" and auth_state:
                mobile_context_options["storage_state"] = auth_state
            elif auth_config["auth_type"] == "form":
                # Reuse saved auth state for mobile context
                from auth import AUTH_STATE_PATH
                if os.path.exists(AUTH_STATE_PATH):
                    mobile_context_options["storage_state"] = AUTH_STATE_PATH

            mobile_context = browser.new_context(**mobile_context_options)
            for page_info in pages_to_capture:
                result = capture_page(mobile_context, page_info, auth_config, errors, suffix="-mobile")
                if result:
                    page_info["screenshot_mobile_path"] = result
                    write_json(PAGE_MAP_PATH, page_map)
            mobile_context.close()

        browser.close()

    # Save errors
    if errors:
        write_json(ERRORS_PATH, errors)
        log_error(f"{len(errors)} erreur(s) enregistrée(s) dans {ERRORS_PATH}")

    log_success("Captures terminées")


if __name__ == "__main__":
    main()

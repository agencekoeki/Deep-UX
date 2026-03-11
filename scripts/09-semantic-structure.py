#!/usr/bin/env python3
"""09-semantic-structure.py — Extracts real HTML semantic structure from each page.

Reads .audit/.env for credentials and base URL.
Reads .audit/page-map.json for the list of pages.
Outputs .audit/semantic/semantic-{page-id}.json per page.

Usage : python3 scripts/09-semantic-structure.py
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
OUTPUT_DIR = os.path.join(AUDIT_DIR, "semantic")
ERRORS_PATH = os.path.join(AUDIT_DIR, "script-errors.json")

# JavaScript to extract all semantic structure in one pass
EXTRACT_SEMANTIC_JS = """
() => {
    // --- HEADINGS ---
    const headings = [];
    const headingEls = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let hIdx = 0;
    for (const el of headingEls) {
        hIdx++;
        const level = parseInt(el.tagName.substring(1), 10);
        const rect = el.getBoundingClientRect();
        let selector = el.tagName.toLowerCase();
        if (el.id) {
            selector = `${el.tagName.toLowerCase()}#${CSS.escape(el.id)}`;
        } else if (el.className && typeof el.className === 'string' && el.className.trim()) {
            const cls = el.className.trim().split(/\\s+/).slice(0, 2).map(c => '.' + CSS.escape(c)).join('');
            selector = `${el.tagName.toLowerCase()}${cls}`;
        }
        headings.push({
            level: level,
            text: (el.textContent || '').trim().substring(0, 200),
            selector: selector,
            position_y: Math.round(rect.y * 100) / 100
        });
    }

    // --- HEADING HIERARCHY VALIDATION ---
    let hierarchyValid = true;
    const hierarchyIssues = [];
    for (let i = 1; i < headings.length; i++) {
        const prev = headings[i - 1].level;
        const curr = headings[i].level;
        if (curr > prev + 1) {
            hierarchyValid = false;
            hierarchyIssues.push(`H${prev} → H${curr} (saut de niveau, H${prev + 1} manquant) à position y=${headings[i].position_y}`);
        }
    }
    // Check first heading is H1
    if (headings.length > 0 && headings[0].level !== 1) {
        hierarchyValid = false;
        hierarchyIssues.push(`Premier titre est H${headings[0].level} au lieu de H1`);
    }

    // --- LANDMARKS ---
    const hasHeader = document.querySelectorAll('header').length > 0;
    const navs = document.querySelectorAll('nav');
    const hasNav = navs.length > 0;
    const hasMain = document.querySelectorAll('main').length > 0;
    const hasAside = document.querySelectorAll('aside').length > 0;
    const hasFooter = document.querySelectorAll('footer').length > 0;
    const hasArticle = document.querySelectorAll('article').length > 0;
    const hasSection = document.querySelectorAll('section').length > 0;
    const multipleNav = navs.length > 1;

    let navAriaLabels = true;
    if (multipleNav) {
        for (const nav of navs) {
            if (!nav.getAttribute('aria-label') && !nav.getAttribute('aria-labelledby')) {
                navAriaLabels = false;
                break;
            }
        }
    } else if (navs.length === 1) {
        // Single nav doesn't strictly need aria-label, but check anyway
        navAriaLabels = !!(navs[0].getAttribute('aria-label') || navs[0].getAttribute('aria-labelledby'));
    } else {
        navAriaLabels = false;
    }

    // --- ARIA ROLES ---
    const ariaRoles = [];
    const roledEls = document.querySelectorAll('[role]');
    for (const el of roledEls) {
        const role = el.getAttribute('role');
        // Skip implicit roles that match HTML5 tags
        const tag = el.tagName.toLowerCase();
        const implicitRoles = {
            'header': 'banner', 'nav': 'navigation', 'main': 'main',
            'aside': 'complementary', 'footer': 'contentinfo', 'button': 'button',
            'a': 'link', 'input': 'textbox', 'select': 'listbox'
        };
        if (implicitRoles[tag] === role) continue;

        let selector = tag;
        if (el.id) {
            selector = `${tag}#${CSS.escape(el.id)}`;
        } else if (el.className && typeof el.className === 'string' && el.className.trim()) {
            const cls = el.className.trim().split(/\\s+/).slice(0, 2).map(c => '.' + CSS.escape(c)).join('');
            selector = `${tag}${cls}`;
        }
        const hasAccessibleName = !!(el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.getAttribute('title') || (el.textContent || '').trim());
        ariaRoles.push({
            role: role,
            selector: selector,
            has_accessible_name: hasAccessibleName
        });
    }

    // --- SKIP LINKS ---
    const skipLinks = [];
    const skipSelectors = 'a[href="#main-content"], a[href="#skip"], a[href="#content"], a[href="#main"], .skip-link, .skip-nav, [class*="skip"]';
    const skipEls = document.querySelectorAll(skipSelectors);
    for (const el of skipEls) {
        if (el.tagName.toLowerCase() !== 'a') continue;
        const href = el.getAttribute('href') || '';
        // Check if visible on focus (common pattern: offscreen until focused)
        const style = window.getComputedStyle(el);
        const isHidden = style.position === 'absolute' && (
            parseInt(style.left) < -100 || parseInt(style.top) < -100 ||
            style.clip === 'rect(0px, 0px, 0px, 0px)' || style.clipPath === 'inset(50%)'
        );
        skipLinks.push({
            text: (el.textContent || '').trim().substring(0, 100),
            target: href,
            visible_on_focus: isHidden  // If hidden normally, assume visible on focus
        });
    }

    // --- LANG ATTRIBUTE ---
    const langValue = document.documentElement.lang || null;

    // --- IMAGES ---
    const imgs = document.querySelectorAll('img');
    let withAlt = 0;
    let withEmptyAlt = 0;
    let withoutAlt = 0;
    const missingAltSelectors = [];
    for (const img of imgs) {
        if (img.hasAttribute('alt')) {
            if (img.alt === '') {
                withEmptyAlt++;
            } else {
                withAlt++;
            }
        } else {
            withoutAlt++;
            let selector = 'img';
            if (img.id) {
                selector = `img#${CSS.escape(img.id)}`;
            } else if (img.src) {
                const src = img.getAttribute('src') || '';
                const short = src.substring(src.lastIndexOf('/') + 1).substring(0, 50);
                selector = `img[src*="${short}"]`;
            } else if (img.className && typeof img.className === 'string' && img.className.trim()) {
                const cls = img.className.trim().split(/\\s+/).slice(0, 2).map(c => '.' + CSS.escape(c)).join('');
                selector = `img${cls}`;
            }
            missingAltSelectors.push(selector);
        }
    }

    // --- FORMS ---
    const forms = [];
    const formEls = document.querySelectorAll('form');
    // Also handle pages with no <form> but still have inputs
    const formContainers = formEls.length > 0 ? formEls : [document.body];
    const isActualForm = formEls.length > 0;

    for (const form of (isActualForm ? formEls : [])) {
        const fields = form.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), select, textarea');
        let withLabel = 0;
        let withoutLabel = 0;
        const unlabeledSelectors = [];

        for (const field of fields) {
            const hasLabel = !!(
                field.id && document.querySelector(`label[for="${CSS.escape(field.id)}"]`) ||
                field.getAttribute('aria-label') ||
                field.getAttribute('aria-labelledby') ||
                field.closest('label')
            );
            if (hasLabel) {
                withLabel++;
            } else {
                withoutLabel++;
                let sel = field.tagName.toLowerCase();
                if (field.id) sel = `${sel}#${CSS.escape(field.id)}`;
                else if (field.name) sel = `${sel}[name="${field.name}"]`;
                unlabeledSelectors.push(sel);
            }
        }

        let formSelector = 'form';
        if (form.id) {
            formSelector = `form#${CSS.escape(form.id)}`;
        } else if (form.action) {
            formSelector = `form[action="${form.getAttribute('action')}"]`;
        }

        forms.push({
            selector: formSelector,
            fields_count: fields.length,
            fields_with_label: withLabel,
            fields_without_label: withoutLabel,
            unlabeled_selectors: unlabeledSelectors
        });
    }

    return {
        headings: headings,
        heading_hierarchy_valid: hierarchyValid,
        heading_hierarchy_issues: hierarchyIssues,
        landmarks: {
            header: hasHeader,
            nav: hasNav,
            main: hasMain,
            aside: hasAside,
            footer: hasFooter,
            article: hasArticle,
            section: hasSection,
            multiple_nav: multipleNav,
            nav_aria_labels: navAriaLabels
        },
        aria_roles: ariaRoles,
        skip_links: skipLinks,
        lang_attribute: {
            present: langValue !== null && langValue !== '',
            value: langValue
        },
        images: {
            total: imgs.length,
            with_alt: withAlt,
            with_empty_alt: withEmptyAlt,
            without_alt: withoutAlt,
            missing_alt_selectors: missingAltSelectors
        },
        forms: forms
    };
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


async def analyze_page(context, page_info, auth_config, errors):
    """Extracts semantic structure from a single page."""
    page_id = page_info["id"]
    output_path = os.path.join(OUTPUT_DIR, f"semantic-{page_id}.json")

    # Idempotent: skip if output already exists
    if os.path.exists(output_path):
        log_skip(f"{page_id} — semantic déjà analysé")
        return

    # Skip parameterized routes
    if page_info.get("parameterized"):
        msg = f"Route paramétrée skippée : {page_info['url_or_path']}"
        log_error(f"{page_id} — {msg}")
        errors.append({
            "script": "09-semantic-structure",
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
        log_step(f"Semantic analysis : {page_id} → {url}")
        timeout = auth_config["playwright_timeout_ms"]
        await page.goto(url, wait_until="networkidle", timeout=timeout)

        semantic_data = await page.evaluate(EXTRACT_SEMANTIC_JS)

        result = {
            "page_id": page_id,
            "url": url,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "headings": semantic_data["headings"],
            "heading_hierarchy_valid": semantic_data["heading_hierarchy_valid"],
            "heading_hierarchy_issues": semantic_data["heading_hierarchy_issues"],
            "landmarks": semantic_data["landmarks"],
            "aria_roles": semantic_data["aria_roles"],
            "skip_links": semantic_data["skip_links"],
            "lang_attribute": semantic_data["lang_attribute"],
            "images": semantic_data["images"],
            "forms": semantic_data["forms"],
        }

        write_json(output_path, result)

        h_count = len(semantic_data["headings"])
        h_valid = "valide" if semantic_data["heading_hierarchy_valid"] else "invalide"
        landmarks_present = sum(1 for v in semantic_data["landmarks"].values() if v is True)
        img_issues = semantic_data["images"]["without_alt"]
        log_success(f"{page_id} — {h_count} headings ({h_valid}), {landmarks_present} landmarks, {img_issues} img sans alt")

    except Exception as e:
        error_msg = str(e)
        log_error(f"{page_id} — {error_msg}")
        errors.append({
            "script": "09-semantic-structure",
            "page_id": page_id,
            "url": url,
            "error": error_msg,
            "error_type": "analysis_failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    finally:
        await page.close()


async def main():
    log_phase(2, "Semantic Structure", inputs=[PAGE_MAP_PATH, ".audit/.env"], outputs=[OUTPUT_DIR])

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

        # Analyze each page
        for page_info in pages_to_scan:
            await analyze_page(context, page_info, auth_config, errors)

        await context.close()
        await browser.close()

    # Save errors
    if errors:
        write_json(ERRORS_PATH, errors)
        log_error(f"{len(errors)} erreur(s) enregistrée(s) dans {ERRORS_PATH}")

    log_success("Semantic structure analysis terminée")


if __name__ == "__main__":
    asyncio.run(main())

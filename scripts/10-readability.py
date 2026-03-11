#!/usr/bin/env python3
"""10-readability.py — Analyse la lisibilité des blocs de texte de chaque page.

Reads .audit/.env for credentials and base URL.
Reads .audit/page-map.json for the list of pages.
Outputs .audit/readability/readability-{page-id}.json per page.

Formule Flesch-Kincaid adaptée au français :
  FK_FR = 207 - 1.015 × (mots / phrases) - 73.6 × (syllabes / mots)

Si pyphen est installé, utilise la syllabification française exacte.
Sinon, utilise une estimation heuristique (voyelles consécutives = 1 syllabe).

Usage : python3 scripts/10-readability.py
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.lib.file_utils import read_json, write_json, ensure_dir
from scripts.lib.progress import log_phase, log_step, log_success, log_error, log_skip
from scripts.lib.auth import load_env, get_auth_config, load_auth_state, save_auth_state

AUDIT_DIR = ".audit"
PAGE_MAP_PATH = os.path.join(AUDIT_DIR, "page-map.json")
OUTPUT_DIR = os.path.join(AUDIT_DIR, "readability")
ERRORS_PATH = os.path.join(AUDIT_DIR, "script-errors.json")

# Minimum word count for a text block to be analyzed
MIN_BLOCK_WORDS = 50

# Try to import pyphen for accurate French syllable counting
try:
    import pyphen
    _dic = pyphen.Pyphen(lang="fr_FR")

    def count_syllables(word):
        """Count syllables using pyphen French dictionary."""
        parts = _dic.inserted(word).split("-")
        return max(1, len(parts))

    SYLLABLE_METHOD = "pyphen"
except ImportError:
    def count_syllables(word):
        """Heuristic syllable count: count vowel groups."""
        word = word.lower()
        vowels = "aeiouyàâéèêëïîôùûüæœ"
        count = 0
        in_vowel = False
        for ch in word:
            if ch in vowels:
                if not in_vowel:
                    count += 1
                    in_vowel = True
            else:
                in_vowel = False
        # Silent e at end in French
        if word.endswith("e") and count > 1:
            count -= 1
        return max(1, count)

    SYLLABLE_METHOD = "heuristic"


def split_sentences(text):
    """Split text into sentences using punctuation."""
    sentences = re.split(r'[.!?]+(?:\s|$)', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def split_words(text):
    """Split text into words."""
    return [w for w in re.findall(r"[a-zA-ZÀ-ÿ'']+", text) if len(w) > 0]


def flesch_kincaid_fr(avg_sentence_length, avg_syllables_per_word):
    """Compute Flesch-Kincaid score adapted for French."""
    score = 207.0 - 1.015 * avg_sentence_length - 73.6 * avg_syllables_per_word
    return round(max(0, min(100, score)), 1)


def reading_level(fk_score):
    """Classify reading level from FK score."""
    if fk_score >= 60:
        return "accessible"
    elif fk_score >= 40:
        return "moderate"
    elif fk_score >= 30:
        return "difficult"
    else:
        return "very_difficult"


# JavaScript to extract text blocks and CTA/labels from the page
EXTRACT_TEXT_JS = """
() => {
    // --- TEXT BLOCKS (>50 words) ---
    const blocks = [];
    const seen = new Set();
    let blockIdx = 0;

    const allTextEls = document.querySelectorAll(
        'p, li, td, th, blockquote, figcaption, article, section > div, ' +
        '.content, .text, [role="main"], main, .description, .summary, .body-text'
    );

    for (const el of allTextEls) {
        const text = (el.innerText || el.textContent || '').trim();
        if (!text || seen.has(text)) continue;

        const words = text.split(/\\s+/).filter(w => w.length > 0);
        if (words.length < 20) continue;

        const isNav = el.closest('nav, header, footer, [role="navigation"], [role="banner"]');

        seen.add(text);
        blockIdx++;

        let selector = el.tagName.toLowerCase();
        if (el.id) {
            selector = `${el.tagName.toLowerCase()}#${CSS.escape(el.id)}`;
        } else if (el.className && typeof el.className === 'string' && el.className.trim()) {
            const cls = el.className.trim().split(/\\s+/).slice(0, 2).map(c => '.' + CSS.escape(c)).join('');
            selector = `${el.tagName.toLowerCase()}${cls}`;
        }

        blocks.push({
            id: `block-${blockIdx}`,
            selector: selector,
            text: text.substring(0, 5000),
            is_navigation: !!isNav
        });
    }

    // --- CTAs AND LABELS ---
    const ctas = [];

    // Buttons
    const buttons = document.querySelectorAll('button, [role="button"], input[type="submit"], input[type="button"], .btn, .button');
    for (const btn of buttons) {
        const text = (btn.innerText || btn.value || btn.textContent || '').trim();
        if (!text || text.length > 100) continue;
        let selector = btn.tagName.toLowerCase();
        if (btn.id) selector = `${btn.tagName.toLowerCase()}#${CSS.escape(btn.id)}`;
        ctas.push({ selector, text: text.substring(0, 100), type: 'button' });
    }

    // Links
    const links = document.querySelectorAll('a[href]');
    for (const a of links) {
        const text = (a.innerText || a.textContent || '').trim();
        if (!text || text.length > 100 || text.length < 2) continue;
        const isProminent = a.closest('nav') || a.classList.contains('btn') || a.classList.contains('cta') || a.classList.contains('button');
        if (!isProminent && links.length > 50) continue;
        let selector = a.tagName.toLowerCase();
        if (a.id) selector = `a#${CSS.escape(a.id)}`;
        ctas.push({ selector, text: text.substring(0, 100), type: 'link' });
    }

    // Headings
    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    for (const h of headings) {
        const text = (h.innerText || h.textContent || '').trim();
        if (!text) continue;
        let selector = h.tagName.toLowerCase();
        if (h.id) selector = `${h.tagName.toLowerCase()}#${CSS.escape(h.id)}`;
        ctas.push({ selector, text: text.substring(0, 200), type: 'heading' });
    }

    // Form labels
    const labels = document.querySelectorAll('label');
    for (const lbl of labels) {
        const text = (lbl.innerText || lbl.textContent || '').trim();
        if (!text) continue;
        let selector = 'label';
        if (lbl.htmlFor) selector = `label[for="${CSS.escape(lbl.htmlFor)}"]`;
        ctas.push({ selector, text: text.substring(0, 100), type: 'label' });
    }

    // Placeholders
    const inputs = document.querySelectorAll('input[placeholder], textarea[placeholder]');
    for (const inp of inputs) {
        const text = (inp.placeholder || '').trim();
        if (!text) continue;
        let selector = inp.tagName.toLowerCase();
        if (inp.id) selector = `${inp.tagName.toLowerCase()}#${CSS.escape(inp.id)}`;
        ctas.push({ selector, text: text.substring(0, 100), type: 'placeholder' });
    }

    return { blocks, ctas };
}
"""


def analyze_block(block_data):
    """Analyze a single text block for readability metrics."""
    text = block_data["text"]
    words = split_words(text)
    word_count = len(words)

    if word_count < MIN_BLOCK_WORDS:
        return None

    sentences = split_sentences(text)
    sentence_count = max(1, len(sentences))

    avg_sentence_length = round(word_count / sentence_count, 1)
    avg_word_length = round(sum(len(w) for w in words) / word_count, 1)

    # Count long sentences (>25 words)
    long_sentences = 0
    for s in sentences:
        s_words = split_words(s)
        if len(s_words) > 25:
            long_sentences += 1

    # Syllable analysis
    total_syllables = sum(count_syllables(w) for w in words)
    avg_syllables_per_word = total_syllables / word_count

    fk_score = flesch_kincaid_fr(avg_sentence_length, avg_syllables_per_word)
    level = reading_level(fk_score)

    return {
        "id": block_data["id"],
        "selector": block_data["selector"],
        "text_sample": text[:100],
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_sentence_length": avg_sentence_length,
        "avg_word_length": avg_word_length,
        "long_sentences_count": long_sentences,
        "flesch_kincaid_fr": fk_score,
        "reading_level": level,
    }


def analyze_ctas(ctas_raw):
    """Classify CTAs and count verb-starting ones."""
    fr_verb_starters = {
        "ajouter", "afficher", "aller", "annuler", "appliquer", "chercher",
        "choisir", "cliquer", "commander", "commencer", "confirmer", "connecter",
        "consulter", "continuer", "copier", "créer", "découvrir", "demander",
        "démarrer", "enregistrer", "envoyer", "essayer", "exporter", "fermer",
        "filtrer", "gérer", "importer", "inscrire", "installer", "lancer",
        "lire", "modifier", "naviguer", "obtenir", "ouvrir", "partager",
        "payer", "personnaliser", "planifier", "profiter", "rechercher",
        "recevoir", "réinitialiser", "rejoindre", "réserver", "retour",
        "sauvegarder", "sélectionner", "soumettre", "supprimer", "télécharger",
        "tester", "tout", "trouver", "valider", "vérifier", "voir",
        "ajoutez", "allez", "annulez", "appliquez", "cherchez", "choisissez",
        "cliquez", "commencez", "confirmez", "connectez", "consultez",
        "continuez", "copiez", "créez", "découvrez", "démarrez", "envoyez",
        "essayez", "exportez", "fermez", "filtrez", "gérez", "importez",
        "inscrivez", "installez", "lancez", "lisez", "modifiez", "obtenez",
        "ouvrez", "partagez", "payez", "profitez", "recherchez", "recevez",
        "réinitialisez", "rejoignez", "réservez", "sauvegardez", "sélectionnez",
        "soumettez", "supprimez", "téléchargez", "testez", "trouvez",
        "validez", "vérifiez", "voyez",
        "add", "apply", "back", "book", "browse", "buy", "cancel", "change",
        "check", "choose", "click", "close", "confirm", "connect", "continue",
        "copy", "create", "delete", "discover", "download", "edit", "enter",
        "explore", "export", "filter", "find", "get", "go", "import", "install",
        "join", "launch", "learn", "log", "manage", "open", "order", "pay",
        "read", "register", "remove", "reset", "retry", "return", "save",
        "search", "see", "select", "send", "share", "show", "sign", "start",
        "submit", "subscribe", "switch", "test", "try", "update", "upload",
        "validate", "verify", "view",
    }

    results = []
    verbs_count = 0
    total_ctas = 0

    for cta in ctas_raw:
        text = cta.get("text", "").strip()
        cta_type = cta.get("type", "other")
        if not text:
            continue

        entry = {
            "selector": cta.get("selector", ""),
            "text": text,
            "type": cta_type,
        }
        results.append(entry)

        if cta_type in ("button", "link"):
            total_ctas += 1
            first_word = text.split()[0].lower().rstrip(".,!?:;") if text.split() else ""
            if first_word in fr_verb_starters:
                verbs_count += 1

    return results, total_ctas, verbs_count


async def process_page(browser, page_data, auth_config, auth_state, base_url):
    """Process a single page for readability analysis."""
    page_id = page_data.get("id", "unknown")
    url = page_data.get("url", "")

    if not url:
        log_skip(f"Page {page_id}: no URL")
        return None

    if url.startswith("/"):
        url = base_url.rstrip("/") + url
    elif not url.startswith("http"):
        url = base_url.rstrip("/") + "/" + url.lstrip("/")

    output_path = os.path.join(OUTPUT_DIR, f"readability-{page_id}.json")

    log_step(f"Analyzing readability: {page_id} → {url}")

    context = None
    try:
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
        )
        page = await context.new_page()

        if auth_config.get("type") == "cookie" and auth_state.get("cookies"):
            await context.add_cookies(auth_state["cookies"])

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            except Exception as e:
                log_error(f"Page {page_id}: navigation failed — {e}")
                return None

        if auth_config.get("type") == "form" and not auth_state.get("authenticated"):
            login_url = auth_config.get("login_url", "")
            if login_url:
                try:
                    await page.goto(login_url, wait_until="networkidle", timeout=15000)
                    username_sel = auth_config.get("username_selector", "#username")
                    password_sel = auth_config.get("password_selector", "#password")
                    submit_sel = auth_config.get("submit_selector", "button[type='submit']")
                    await page.fill(username_sel, auth_config.get("username", ""))
                    await page.fill(password_sel, auth_config.get("password", ""))
                    await page.click(submit_sel)
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    cookies = await context.cookies()
                    auth_state["cookies"] = cookies
                    auth_state["authenticated"] = True
                    save_auth_state(auth_state)
                    await page.goto(url, wait_until="networkidle", timeout=15000)
                except Exception as e:
                    log_error(f"Page {page_id}: login failed — {e}")

        await page.wait_for_timeout(1000)

        try:
            raw_data = await page.evaluate(EXTRACT_TEXT_JS)
        except Exception as e:
            log_error(f"Page {page_id}: text extraction failed — {e}")
            return None

        raw_blocks = raw_data.get("blocks", [])
        raw_ctas = raw_data.get("ctas", [])

        content_blocks = [b for b in raw_blocks if not b.get("is_navigation", False)]
        analyzed_blocks = []
        for block in content_blocks:
            result = analyze_block(block)
            if result:
                analyzed_blocks.append(result)

        ctas_list, total_ctas, verbs_count = analyze_ctas(raw_ctas)

        total_words = sum(b["word_count"] for b in analyzed_blocks)
        avg_fk = 0
        dominant_level = "accessible"
        if analyzed_blocks:
            avg_fk = round(
                sum(b["flesch_kincaid_fr"] for b in analyzed_blocks) / len(analyzed_blocks), 1
            )
            dominant_level = reading_level(avg_fk)

        lang = "unknown"
        try:
            lang = await page.evaluate("() => document.documentElement.lang || 'unknown'")
        except Exception:
            pass

        result = {
            "page_id": page_id,
            "url": url,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "language_detected": lang,
            "syllable_method": SYLLABLE_METHOD,
            "blocks": analyzed_blocks,
            "ctas_and_labels": ctas_list,
            "global_summary": {
                "total_words": total_words,
                "blocks_analyzed": len(analyzed_blocks),
                "avg_flesch_fr": avg_fk,
                "dominant_reading_level": dominant_level,
                "ctas_count": total_ctas,
                "ctas_starting_with_verb": verbs_count,
            },
        }

        write_json(output_path, result)
        log_success(
            f"Page {page_id}: {len(analyzed_blocks)} blocks, "
            f"FK={avg_fk}, level={dominant_level}, "
            f"{total_ctas} CTAs ({verbs_count} verb-first)"
        )
        return result

    except Exception as e:
        log_error(f"Page {page_id}: unexpected error — {e}")
        return None
    finally:
        if context:
            await context.close()


async def main():
    log_phase("10-readability", f"Analyse de lisibilité (syllabification : {SYLLABLE_METHOD})")

    env = load_env()
    base_url = env.get("BASE_URL", "http://localhost:3000")
    auth_config = get_auth_config(env)
    auth_state = load_auth_state()

    if not os.path.exists(PAGE_MAP_PATH):
        log_error(f"{PAGE_MAP_PATH} not found — run 03-build-page-map.py first")
        sys.exit(1)

    page_map = read_json(PAGE_MAP_PATH)
    pages = page_map.get("pages", [])
    if not pages:
        log_error("No pages found in page-map.json")
        sys.exit(1)

    ensure_dir(OUTPUT_DIR)
    log_step(f"Pages to analyze: {len(pages)}")

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        log_error("playwright not installed — pip install playwright")
        sys.exit(1)

    errors = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            for page_data in pages:
                try:
                    result = await process_page(
                        browser, page_data, auth_config, auth_state, base_url
                    )
                    if result is None:
                        errors.append({
                            "page_id": page_data.get("id", "unknown"),
                            "error": "processing returned None",
                        })
                except Exception as e:
                    errors.append({
                        "page_id": page_data.get("id", "unknown"),
                        "error": str(e),
                    })
        finally:
            await browser.close()

    if errors:
        existing_errors = []
        if os.path.exists(ERRORS_PATH):
            try:
                existing_errors = read_json(ERRORS_PATH)
                if not isinstance(existing_errors, list):
                    existing_errors = [existing_errors]
            except Exception:
                existing_errors = []
        existing_errors.append({
            "script": "10-readability.py",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "errors": errors,
        })
        write_json(ERRORS_PATH, existing_errors)

    success_count = len(pages) - len(errors)
    log_success(f"Readability analysis complete: {success_count}/{len(pages)} pages")


if __name__ == "__main__":
    asyncio.run(main())

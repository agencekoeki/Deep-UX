#!/usr/bin/env python3
"""13-contrast-real.py — Mesure les ratios de contraste réels depuis les pixels des screenshots.

N'utilise PAS Playwright — lit les screenshots avec Pillow (PIL) et croise
avec les données DOM/semantic pour localiser les éléments texte.

Usage : python3 scripts/13-contrast-real.py
Inputs : .audit/page-map.json, .audit/screenshots/, .audit/dom/, .audit/semantic/
Output : .audit/contrast-real/contrast-{page-id}.json
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
SCREENSHOTS_DIR = os.path.join(AUDIT_DIR, "screenshots")
DOM_DIR = os.path.join(AUDIT_DIR, "dom")
SEMANTIC_DIR = os.path.join(AUDIT_DIR, "semantic")
OUTPUT_DIR = os.path.join(AUDIT_DIR, "contrast-real")
ERRORS_PATH = os.path.join(AUDIT_DIR, "script-errors.json")


def linearize_channel(c):
    """Linearize a single sRGB channel value (0-255) for luminance calculation."""
    c = c / 255.0
    if c <= 0.03928:
        return c / 12.92
    return ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(r, g, b):
    """Compute WCAG relative luminance from linear RGB."""
    return 0.2126 * linearize_channel(r) + 0.7152 * linearize_channel(g) + 0.0722 * linearize_channel(b)


def contrast_ratio(rgb1, rgb2):
    """Compute WCAG contrast ratio between two RGB tuples."""
    l1 = relative_luminance(*rgb1)
    l2 = relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def is_large_text(font_size_px, font_bold):
    """Determine if text qualifies as 'large text' per WCAG."""
    if font_size_px is None:
        return False
    if font_size_px >= 18:
        return True
    if font_size_px >= 14 and font_bold:
        return True
    return False


def sample_foreground(img, cx, cy):
    """Sample the foreground pixel at center of element."""
    w, h = img.size
    cx = max(0, min(cx, w - 1))
    cy = max(0, min(cy, h - 1))
    pixel = img.getpixel((cx, cy))
    # Handle RGBA or RGB
    return pixel[:3]


def sample_background(img, x, y, width, height, margin=2):
    """Sample background pixels around the element (4 corners slightly outside).

    Returns the average RGB and the variance indicator.
    """
    w, h = img.size
    sample_points = [
        (max(0, x - margin), max(0, y - margin)),                          # top-left
        (min(w - 1, x + width + margin), max(0, y - margin)),             # top-right
        (max(0, x - margin), min(h - 1, y + height + margin)),            # bottom-left
        (min(w - 1, x + width + margin), min(h - 1, y + height + margin)), # bottom-right
    ]

    pixels = []
    for px, py in sample_points:
        px = int(max(0, min(px, w - 1)))
        py = int(max(0, min(py, h - 1)))
        pixel = img.getpixel((px, py))
        pixels.append(pixel[:3])

    if not pixels:
        return (255, 255, 255), False

    # Average
    avg_r = sum(p[0] for p in pixels) // len(pixels)
    avg_g = sum(p[1] for p in pixels) // len(pixels)
    avg_b = sum(p[2] for p in pixels) // len(pixels)

    # Variance: check if bg colors differ significantly
    max_diff = 0
    for i in range(len(pixels)):
        for j in range(i + 1, len(pixels)):
            diff = sum(abs(pixels[i][c] - pixels[j][c]) for c in range(3))
            max_diff = max(max_diff, diff)

    high_variance = max_diff > 100  # Threshold for "complex background"

    return (avg_r, avg_g, avg_b), high_variance


def rgb_to_string(rgb):
    """Convert RGB tuple to string representation."""
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def get_text_elements(page_id):
    """Gather text elements with position data from DOM and semantic files."""
    elements = []

    # Try semantic data first (usually has richer position info)
    semantic_path = os.path.join(SEMANTIC_DIR, f"semantic-{page_id}.json")
    semantic = read_json(semantic_path)
    if semantic and "elements" in semantic:
        for el in semantic["elements"]:
            if el.get("text") and el.get("position"):
                pos = el["position"]
                elements.append({
                    "selector": el.get("selector", "unknown"),
                    "text": el.get("text", "")[:30],
                    "x": pos.get("x", 0),
                    "y": pos.get("y", 0),
                    "width": pos.get("width", 0),
                    "height": pos.get("height", 0),
                    "font_size_px": el.get("font_size_px"),
                    "font_bold": el.get("font_bold", False),
                })

    # Also try DOM inventory
    dom_path = os.path.join(DOM_DIR, f"dom-{page_id}.json")
    dom = read_json(dom_path)
    if dom and "text_elements" in dom:
        seen = set(e["selector"] for e in elements)
        for el in dom["text_elements"]:
            sel = el.get("selector", "")
            if sel not in seen and el.get("position"):
                pos = el["position"]
                elements.append({
                    "selector": sel,
                    "text": el.get("text", "")[:30],
                    "x": pos.get("x", 0),
                    "y": pos.get("y", 0),
                    "width": pos.get("width", 0),
                    "height": pos.get("height", 0),
                    "font_size_px": el.get("font_size_px"),
                    "font_bold": el.get("font_bold", False),
                })

    # Fallback: if semantic has headings/paragraphs
    if semantic and not elements:
        for key in ["headings", "paragraphs", "links"]:
            for el in semantic.get(key, []):
                if el.get("position"):
                    pos = el["position"]
                    elements.append({
                        "selector": el.get("selector", key),
                        "text": el.get("text", "")[:30],
                        "x": pos.get("x", 0),
                        "y": pos.get("y", 0),
                        "width": pos.get("width", 0),
                        "height": pos.get("height", 0),
                        "font_size_px": el.get("font_size_px"),
                        "font_bold": el.get("font_bold", False),
                    })

    return elements


def log_script_error(errors, script, page_id, message):
    """Append error to the shared script-errors list."""
    errors.append({
        "script": script,
        "page_id": page_id,
        "error": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def measure_page_contrast(page_info, errors):
    """Measure real contrast ratios for a single page from its screenshot."""
    from PIL import Image

    page_id = page_info["id"]
    output_path = os.path.join(OUTPUT_DIR, f"contrast-{page_id}.json")

    # Idempotent
    if os.path.exists(output_path):
        log_skip(f"contrast-{page_id}.json")
        return

    # Find screenshot
    screenshot_path = page_info.get("screenshot_path")
    if not screenshot_path or not os.path.exists(screenshot_path):
        # Try default location
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{page_id}.png")
        if not os.path.exists(screenshot_path):
            log_error(f"{page_id} — screenshot introuvable, skip")
            return

    url = page_info.get("url_or_path", "")

    if page_info.get("parameterized"):
        log_skip(f"{page_id} — route paramétrée, skip")
        return

    log_step(f"Contraste réel : {page_id}")

    # Get text elements with positions
    text_elements = get_text_elements(page_id)
    if not text_elements:
        log_error(f"{page_id} — aucun élément texte avec position trouvé, skip")
        log_script_error(errors, "13-contrast-real.py", page_id,
                         "Aucun élément texte avec position trouvé (DOM/semantic manquant)")
        return

    try:
        img = Image.open(screenshot_path).convert("RGB")
    except Exception as e:
        msg = f"Impossible d'ouvrir le screenshot : {e}"
        log_error(f"{page_id} — {msg}")
        log_script_error(errors, "13-contrast-real.py", page_id, msg)
        return

    measurements = []

    for el in text_elements:
        x = int(el.get("x", 0))
        y = int(el.get("y", 0))
        w = int(el.get("width", 0))
        h = int(el.get("height", 0))

        # Skip elements with no size or outside image bounds
        if w <= 0 or h <= 0:
            continue
        if x < 0 or y < 0:
            continue
        if x >= img.size[0] or y >= img.size[1]:
            continue

        # Sample foreground at center
        cx = min(x + w // 2, img.size[0] - 1)
        cy = min(y + h // 2, img.size[1] - 1)
        fg_rgb = sample_foreground(img, cx, cy)

        # Sample background around element
        bg_rgb, high_variance = sample_background(img, x, y, w, h)

        ratio = contrast_ratio(fg_rgb, bg_rgb)
        ratio = round(ratio, 2)

        font_size = el.get("font_size_px")
        font_bold = el.get("font_bold", False)
        large = is_large_text(font_size, font_bold)

        # WCAG thresholds
        aa_threshold = 3.0 if large else 4.5
        aaa_threshold = 4.5 if large else 7.0

        note = None
        if high_variance:
            note = "fond complexe — valeur approximative"

        measurements.append({
            "selector": el["selector"],
            "text_sample": el.get("text", "")[:30],
            "font_size_px": font_size,
            "font_bold": font_bold,
            "fg_color_sampled": rgb_to_string(fg_rgb),
            "bg_color_sampled": rgb_to_string(bg_rgb),
            "contrast_ratio": ratio,
            "wcag_aa": ratio >= aa_threshold,
            "wcag_aaa": ratio >= aaa_threshold,
            "note": note,
        })

    # Summary
    total = len(measurements)
    failing_aa = [m for m in measurements if not m["wcag_aa"]]
    worst = min(measurements, key=lambda m: m["contrast_ratio"]) if measurements else None

    summary = {
        "total_measured": total,
        "failing_wcag_aa": len(failing_aa),
        "failing_wcag_aa_pct": round(len(failing_aa) / total * 100, 1) if total > 0 else 0,
        "worst_ratio": worst["contrast_ratio"] if worst else 0,
        "worst_selector": worst["selector"] if worst else "",
    }

    result = {
        "page_id": page_id,
        "url": url,
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "method": "pixel_sampling",
        "measurements": measurements,
        "summary": summary,
    }

    write_json(output_path, result)
    log_success(
        f"contrast-{page_id}.json — {total} mesures, "
        f"{len(failing_aa)} échecs AA ({summary['failing_wcag_aa_pct']}%)"
    )


def main():
    log_phase("2+", "Real Contrast Audit",
              inputs=[PAGE_MAP_PATH, SCREENSHOTS_DIR, DOM_DIR, SEMANTIC_DIR],
              outputs=[OUTPUT_DIR])

    page_map = read_json(PAGE_MAP_PATH)
    if not page_map:
        log_error(f"{PAGE_MAP_PATH} introuvable — lancez d'abord 03-build-page-map.py")
        sys.exit(1)

    ensure_dir(OUTPUT_DIR)
    errors = read_json(ERRORS_PATH) or []

    # Check Pillow availability
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        log_error("Pillow non installé — pip3 install Pillow")
        log_script_error(errors, "13-contrast-real.py", None,
                         "Pillow (PIL) non installé — pip3 install Pillow")
        if errors:
            write_json(ERRORS_PATH, errors)
        sys.exit(0)  # Exit gracefully as specified

    for page_info in page_map.get("pages", []):
        try:
            measure_page_contrast(page_info, errors)
        except Exception as e:
            msg = str(e)
            log_error(f"{page_info.get('id', '?')} — {msg}")
            log_script_error(errors, "13-contrast-real.py", page_info.get("id"), msg)
            continue  # Continue on failure

    if errors:
        write_json(ERRORS_PATH, errors)

    log_success("Audit contraste réel terminé")


if __name__ == "__main__":
    main()

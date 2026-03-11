#!/usr/bin/env python3
"""05-extract-tokens.py — Extrait tous les design tokens du projet.

Couleurs, typographie, espacements, ombres, border-radius.
Lecture seule sur les fichiers source.

Usage : python3 scripts/05-extract-tokens.py
Output : .audit/design-tokens.json
"""

import os
import re
import sys
import math
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from file_utils import read_json, write_json, ensure_dir
from progress import log_phase, log_step, log_success, log_error, log_skip

AUDIT_DIR = ".audit"
PROJECT_MAP_PATH = os.path.join(AUDIT_DIR, "project-map.json")
OUTPUT_PATH = os.path.join(AUDIT_DIR, "design-tokens.json")

# Regex patterns
HEX_COLOR = re.compile(r"#(?:[0-9a-fA-F]{3,4}){1,2}\b")
RGB_COLOR = re.compile(r"rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+(?:\s*,\s*[\d.]+)?\s*\)")
HSL_COLOR = re.compile(r"hsla?\(\s*\d+\s*,\s*[\d.]+%\s*,\s*[\d.]+%(?:\s*,\s*[\d.]+)?\s*\)")
CSS_VAR_COLOR = re.compile(r"(--[\w-]*(?:color|bg|background|text|border|fill|stroke)[\w-]*)\s*:\s*([^;]+)")
CSS_VAR_ANY = re.compile(r"(--[\w-]+)\s*:\s*([^;]+)")

FONT_FAMILY = re.compile(r"font-family\s*:\s*([^;]+)")
FONT_SIZE = re.compile(r"font-size\s*:\s*([\d.]+(?:px|rem|em|pt|vw|%))")
FONT_WEIGHT = re.compile(r"font-weight\s*:\s*(\d{3}|normal|bold|bolder|lighter)")
LINE_HEIGHT = re.compile(r"line-height\s*:\s*([\d.]+(?:px|rem|em|%)?)")
LETTER_SPACING = re.compile(r"letter-spacing\s*:\s*([^;]+)")

MARGIN_PADDING = re.compile(r"(?:margin|padding|gap)(?:-(?:top|right|bottom|left))?\s*:\s*([^;]+)")
BORDER_RADIUS = re.compile(r"border-radius\s*:\s*([^;]+)")
BOX_SHADOW = re.compile(r"box-shadow\s*:\s*([^;]+)")
Z_INDEX = re.compile(r"z-index\s*:\s*(\d+)")
MEDIA_QUERY = re.compile(r"@media[^{]*\(\s*(?:min|max)-width\s*:\s*([\d.]+(?:px|em|rem))\s*\)")

WEIGHT_MAP = {"normal": 400, "bold": 700, "bolder": 800, "lighter": 300}

GOOGLE_FONTS_IMPORT = re.compile(r"@import\s+url\(['\"]?https://fonts\.googleapis\.com[^)]+['\"]?\)")
GOOGLE_FONTS_LINK = re.compile(r"fonts\.googleapis\.com")


def read_css_files(project_root, files):
    """Lit tous les fichiers CSS/SCSS et retourne leur contenu concaténé."""
    content = ""
    css_files = files.get("css", []) + files.get("scss", [])
    for f in css_files:
        full_path = os.path.join(project_root, f)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                content += fh.read() + "\n"
        except (OSError, IOError):
            continue
    return content


def extract_spacing_values(content):
    """Extrait les valeurs d'espacement (margin, padding, gap)."""
    values = []
    for match in MARGIN_PADDING.finditer(content):
        raw = match.group(1).strip()
        parts = raw.split()
        for part in parts:
            part = part.strip()
            if re.match(r"^[\d.]+px$", part):
                values.append(part)
    return values


def classify_spacing_scale(values):
    """Classifie l'échelle d'espacement."""
    if not values:
        return "chaotic", "0px"
    nums = sorted(set(float(v.replace("px", "")) for v in values if "px" in v))
    if not nums:
        return "chaotic", "0px"

    # Check 4px grid
    if all(n % 4 == 0 for n in nums if n > 0):
        return "4px-grid", "4px"
    # Check 8px grid
    if all(n % 8 == 0 for n in nums if n > 0):
        return "8px-grid", "8px"
    # Check if mostly multiples of 4
    fours = sum(1 for n in nums if n % 4 == 0 and n > 0)
    if fours / max(len(nums), 1) > 0.7:
        return "mixed", "4px"
    return "chaotic", "0px"


def classify_size_scale(sizes):
    """Classifie l'échelle typographique."""
    if len(sizes) <= 2:
        return "consistent"
    nums = sorted(float(s.replace("px", "").replace("rem", "").replace("em", "")) for s in sizes)
    if len(nums) > 10:
        return "chaotic"
    if len(nums) > 6:
        return "loose"
    return "consistent"


def hex_to_rgb(hex_color):
    """Convertit un hex en RGB."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) == 4:
        h = "".join(c * 2 for c in h[:3])
    if len(h) >= 6:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return None


def relative_luminance(r, g, b):
    """Calcule la luminance relative (WCAG)."""
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(color1_rgb, color2_rgb):
    """Calcule le ratio de contraste entre deux couleurs."""
    l1 = relative_luminance(*color1_rgb)
    l2 = relative_luminance(*color2_rgb)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def compute_contrast_pairs(hex_colors):
    """Calcule les ratios de contraste pour les paires courantes."""
    ratios = []
    # Always check against white and near-black
    standard_bgs = ["#ffffff", "#f8f9fa", "#f5f5f5"]
    standard_darks = ["#000000", "#111111", "#212121", "#333333"]

    all_colors = list(set(hex_colors))[:30]  # Limit to avoid explosion

    for fg in all_colors:
        fg_rgb = hex_to_rgb(fg)
        if not fg_rgb:
            continue
        for bg_hex in standard_bgs:
            bg_rgb = hex_to_rgb(bg_hex)
            if not bg_rgb:
                continue
            ratio = contrast_ratio(fg_rgb, bg_rgb)
            if ratio > 1.1:  # Skip near-identical
                ratios.append({
                    "fg": fg,
                    "bg": bg_hex,
                    "ratio": round(ratio, 2),
                    "wcag_aa": ratio >= 4.5,
                    "wcag_aaa": ratio >= 7.0,
                })

    return ratios[:20]  # Keep top 20


def detect_font_source(content, font_name):
    """Détecte la source d'une police."""
    if GOOGLE_FONTS_LINK.search(content) and font_name.lower() in content.lower():
        return "google"
    system_fonts = {"arial", "helvetica", "times", "georgia", "verdana", "courier",
                    "system-ui", "-apple-system", "segoe ui", "roboto", "sans-serif", "serif", "monospace"}
    if font_name.lower().strip("'\"") in system_fonts:
        return "system"
    return "local"


def main():
    log_phase(2, "Extract Design Tokens", inputs=[PROJECT_MAP_PATH], outputs=[OUTPUT_PATH])

    existing = read_json(OUTPUT_PATH)
    if existing:
        log_skip("design-tokens.json déjà existant")
        return

    project_map = read_json(PROJECT_MAP_PATH)
    if not project_map:
        log_error(f"{PROJECT_MAP_PATH} introuvable — lancez d'abord 02-discover.py")
        sys.exit(1)

    project_root = project_map.get("project_root", os.getcwd())
    files = project_map.get("files", {})

    log_step("Lecture des fichiers CSS/SCSS...")
    css_content = read_css_files(project_root, files)
    if not css_content:
        log_error("Aucun fichier CSS/SCSS trouvé")

    # Also read HTML/JSX/TSX for inline styles and Tailwind classes
    for ext in ["html", "jsx", "tsx", "vue"]:
        for f in files.get(ext, []):
            full_path = os.path.join(project_root, f)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                    css_content += fh.read() + "\n"
            except (OSError, IOError):
                continue

    ensure_dir(AUDIT_DIR)

    # --- COLORS ---
    log_step("Extraction des couleurs...")
    hex_colors = HEX_COLOR.findall(css_content)
    rgb_colors = RGB_COLOR.findall(css_content)
    hsl_colors = HSL_COLOR.findall(css_content)
    all_colors = list(set(hex_colors + rgb_colors + hsl_colors))

    css_variables = {}
    for match in CSS_VAR_ANY.finditer(css_content):
        var_name = match.group(1).strip()
        var_value = match.group(2).strip()
        css_variables[var_name] = var_value

    color_vars = {}
    for match in CSS_VAR_COLOR.finditer(css_content):
        color_vars[match.group(1).strip()] = match.group(2).strip()

    has_design_system = len(css_variables) > 10

    # Classify colors (simplified)
    primary_colors = [c for c in hex_colors if c.lower() not in ("#fff", "#ffffff", "#000", "#000000", "#333", "#333333", "#666", "#666666", "#999", "#999999", "#ccc", "#cccccc", "#eee", "#eeeeee", "#f5f5f5", "#f8f9fa")]
    neutral_colors = [c for c in hex_colors if c.lower() in ("#fff", "#ffffff", "#000", "#000000", "#333", "#333333", "#666", "#666666", "#999", "#999999", "#ccc", "#cccccc", "#eee", "#eeeeee", "#f5f5f5", "#f8f9fa")]

    # Semantic colors heuristic
    semantic = {"success": None, "error": None, "warning": None}
    for var, val in color_vars.items():
        var_lower = var.lower()
        if "success" in var_lower or "green" in var_lower:
            semantic["success"] = val
        if "error" in var_lower or "danger" in var_lower or "red" in var_lower:
            semantic["error"] = val
        if "warning" in var_lower or "yellow" in var_lower or "orange" in var_lower:
            semantic["warning"] = val

    log_success(f"{len(all_colors)} couleurs, {len(css_variables)} variables CSS")

    # --- TYPOGRAPHY ---
    log_step("Extraction de la typographie...")
    families_raw = FONT_FAMILY.findall(css_content)
    families = []
    seen_families = set()
    for fam_str in families_raw:
        for fam in fam_str.split(","):
            fam = fam.strip().strip("'\"")
            if fam and fam.lower() not in seen_families:
                seen_families.add(fam.lower())
                families.append(fam)

    weights_raw = FONT_WEIGHT.findall(css_content)
    weights_all = []
    for w in weights_raw:
        if w in WEIGHT_MAP:
            weights_all.append(WEIGHT_MAP[w])
        else:
            try:
                weights_all.append(int(w))
            except ValueError:
                pass

    font_families = []
    for fam in families[:10]:  # Limit
        fam_weights = sorted(set(weights_all)) or [400]
        source = detect_font_source(css_content, fam)
        font_families.append({"name": fam, "weights": fam_weights, "source": source})

    sizes = sorted(set(FONT_SIZE.findall(css_content)))
    line_heights = sorted(set(LINE_HEIGHT.findall(css_content)))
    size_scale = classify_size_scale(sizes)

    # Dominant sizes
    size_counter = Counter(FONT_SIZE.findall(css_content))
    dominant_body = size_counter.most_common(1)[0][0] if size_counter else "16px"
    large_sizes = [(s, c) for s, c in size_counter.items() if float(re.match(r"[\d.]+", s).group()) >= 20]
    dominant_heading = max(large_sizes, key=lambda x: x[1])[0] if large_sizes else "32px"

    log_success(f"{len(font_families)} famille(s), {len(sizes)} taille(s)")

    # --- SPACING ---
    log_step("Extraction des espacements...")
    spacing_values = extract_spacing_values(css_content)
    unique_spacing = sorted(set(spacing_values), key=lambda v: float(v.replace("px", "")) if "px" in v else 0)
    scale_type, base_unit = classify_spacing_scale(unique_spacing)
    log_success(f"{len(unique_spacing)} valeurs, échelle : {scale_type}")

    # --- BORDERS ---
    log_step("Extraction des bordures et ombres...")
    radius_values = sorted(set(BORDER_RADIUS.findall(css_content)))
    border_styles = []

    # --- SHADOWS ---
    shadows = sorted(set(BOX_SHADOW.findall(css_content)))[:10]

    # --- BREAKPOINTS ---
    breakpoints = sorted(set(MEDIA_QUERY.findall(css_content)))

    # --- CONTRAST ---
    log_step("Calcul des ratios de contraste...")
    contrast_ratios = compute_contrast_pairs(list(set(hex_colors)))
    log_success(f"{len(contrast_ratios)} paires évaluées")

    # --- TOKEN COHERENCE ---
    coherence = 0
    if has_design_system:
        coherence += 30
    if scale_type in ("4px-grid", "8px-grid"):
        coherence += 20
    if size_scale == "consistent":
        coherence += 20
    elif size_scale == "loose":
        coherence += 10
    if len(font_families) <= 3:
        coherence += 15
    if len(color_vars) > 5:
        coherence += 15

    # --- OUTPUT ---
    tokens = {
        "colors": {
            "primary": list(set(primary_colors))[:20],
            "neutral": list(set(neutral_colors)),
            "semantic": semantic,
            "all_values": all_colors[:50],
            "css_variables": color_vars,
            "has_design_system": has_design_system,
        },
        "typography": {
            "font_families": font_families,
            "sizes_used": sizes,
            "size_scale": size_scale,
            "line_heights_used": line_heights,
            "dominant_body_size": dominant_body,
            "dominant_heading_size": dominant_heading,
        },
        "spacing": {
            "values_used": unique_spacing[:30],
            "scale_type": scale_type,
            "base_unit": base_unit,
        },
        "borders": {
            "radius_values": radius_values[:15],
            "border_styles": border_styles,
        },
        "shadows": shadows,
        "breakpoints": breakpoints,
        "contrast_ratios": contrast_ratios,
        "token_coherence_score": min(coherence, 100),
    }

    write_json(OUTPUT_PATH, tokens)
    log_success(f"Écrit : {OUTPUT_PATH}")
    log_success(f"Score de cohérence des tokens : {coherence}/100")


if __name__ == "__main__":
    main()

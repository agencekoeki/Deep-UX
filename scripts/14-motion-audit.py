#!/usr/bin/env python3
"""14-motion-audit.py — Parse CSS/SCSS pour auditer animations et transitions.

N'utilise PAS Playwright — parsing pur de fichiers CSS/SCSS.
Détecte les animations longues, transitions sur éléments interactifs,
et vérifie la couverture prefers-reduced-motion.

Usage : python3 scripts/14-motion-audit.py
Inputs : .audit/project-map.json
Output : .audit/motion/motion-audit.json
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
PROJECT_MAP_PATH = os.path.join(AUDIT_DIR, "project-map.json")
OUTPUT_DIR = os.path.join(AUDIT_DIR, "motion")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "motion-audit.json")
ERRORS_PATH = os.path.join(AUDIT_DIR, "script-errors.json")

# Interactive selector patterns (substring match in CSS selectors)
INTERACTIVE_PATTERNS = ["button", "a", "input", ".btn", '[role="button"]', "[role='button']",
                        ":hover", ":focus", ":active"]

# Regex patterns
RE_KEYFRAMES = re.compile(
    r'@keyframes\s+([\w-]+)\s*\{',
    re.MULTILINE
)

RE_ANIMATION_PROPERTY = re.compile(
    r'animation(?:-name)?\s*:\s*([^;]+)',
    re.MULTILINE
)

RE_ANIMATION_DURATION = re.compile(
    r'animation-duration\s*:\s*([\d.]+(?:m?s))',
    re.MULTILINE
)

RE_ANIMATION_SHORTHAND = re.compile(
    r'animation\s*:\s*([^;]+)',
    re.MULTILINE
)

RE_ANIMATION_ITERATION = re.compile(
    r'animation-iteration-count\s*:\s*([\w]+)',
    re.MULTILINE
)

RE_TRANSITION = re.compile(
    r'transition\s*:\s*([^;]+)',
    re.MULTILINE
)

RE_TRANSITION_PROPERTY = re.compile(
    r'transition-property\s*:\s*([^;]+)',
    re.MULTILINE
)

RE_TRANSITION_DURATION = re.compile(
    r'transition-duration\s*:\s*([\d.]+(?:m?s))',
    re.MULTILINE
)

RE_REDUCED_MOTION = re.compile(
    r'@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)\s*\{',
    re.MULTILINE
)

RE_SELECTOR_BLOCK = re.compile(
    r'([^{}]+?)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
    re.DOTALL
)

DURATION_RE = re.compile(r'([\d.]+)(m?s)')


def parse_duration_ms(value):
    """Parse a CSS duration string to milliseconds."""
    match = DURATION_RE.search(value)
    if not match:
        return 0
    num = float(match.group(1))
    unit = match.group(2)
    if unit == 's':
        return num * 1000
    return num  # Already ms


def extract_duration_from_shorthand(shorthand):
    """Extract duration from animation/transition shorthand value."""
    # The first time-like value is the duration
    match = DURATION_RE.search(shorthand)
    if match:
        return parse_duration_ms(match.group(0))
    return 0


def is_interactive_selector(selector):
    """Check if a CSS selector refers to an interactive element."""
    sel_lower = selector.lower()
    for pattern in INTERACTIVE_PATTERNS:
        if pattern.lower() in sel_lower:
            return True
    return False


def get_current_selector(content, position):
    """Find the CSS selector that contains the given position in the content.

    Walks backwards from position to find the enclosing rule's selector.
    """
    # Find the last '{' before position
    brace_pos = content.rfind('{', 0, position)
    if brace_pos == -1:
        return "unknown"

    # Walk backwards from brace to find selector (skip whitespace and comments)
    before = content[:brace_pos].rstrip()

    # Find the last '}' or start of file to delimit the selector
    prev_close = before.rfind('}')
    prev_semicol = before.rfind(';')
    start = max(prev_close, prev_semicol) + 1

    selector = before[start:].strip()
    # Clean up: remove @media wrapper if present
    if '@media' in selector:
        # Find the last selector after the media block opening
        last_brace = selector.rfind('{')
        if last_brace >= 0:
            selector = selector[last_brace + 1:].strip()

    # Truncate very long selectors
    if len(selector) > 120:
        selector = selector[:120] + "..."

    return selector or "unknown"


def find_line_number(content, position):
    """Find the line number for a character position."""
    return content[:position].count('\n') + 1


def read_css_files(project_map):
    """Read all CSS/SCSS files from the project map."""
    project_root = project_map.get("project_root", os.getcwd())
    files_dict = project_map.get("files", {})
    css_files = files_dict.get("css", []) + files_dict.get("scss", [])

    file_contents = []
    for f in css_files:
        full_path = os.path.join(project_root, f)
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                file_contents.append((f, fh.read()))
        except (OSError, IOError):
            continue

    return file_contents


def extract_keyframes_names_in_reduced_motion(content):
    """Find animation/keyframe names referenced inside @media (prefers-reduced-motion) blocks."""
    covered_names = set()

    # Find all reduced motion media query blocks
    for match in RE_REDUCED_MOTION.finditer(content):
        start = match.end()
        # Find the matching closing brace
        depth = 1
        pos = start
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1

        block = content[start:pos]

        # Find animation names referenced in this block
        for anim_match in RE_ANIMATION_PROPERTY.finditer(block):
            val = anim_match.group(1).strip()
            # Extract animation name (first word that's not a keyword)
            for word in val.split():
                word = word.strip(',')
                if word and word not in ('none', 'initial', 'inherit', 'unset',
                                         'ease', 'ease-in', 'ease-out', 'ease-in-out',
                                         'linear', 'infinite', 'forwards', 'backwards',
                                         'both', 'normal', 'reverse', 'alternate',
                                         'alternate-reverse', 'running', 'paused'):
                    if not DURATION_RE.match(word):
                        covered_names.add(word)

        # Also check for animation: none or transition: none patterns
        if 'animation: none' in block or 'animation:none' in block:
            covered_names.add('__all__')
        if 'transition: none' in block or 'transition:none' in block:
            covered_names.add('__transitions_all__')

    return covered_names


def log_script_error(errors_list, script, page_id, message):
    """Append error to the shared script-errors list."""
    errors_list.append({
        "script": script,
        "page_id": page_id,
        "error": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def main():
    log_phase("2+", "Motion & Animation Audit",
              inputs=[PROJECT_MAP_PATH],
              outputs=[OUTPUT_PATH])

    # Idempotent
    if os.path.exists(OUTPUT_PATH):
        log_skip("motion-audit.json")
        return

    project_map = read_json(PROJECT_MAP_PATH)
    if not project_map:
        log_error(f"{PROJECT_MAP_PATH} introuvable — lancez d'abord 02-discover.py")
        sys.exit(1)

    ensure_dir(OUTPUT_DIR)
    errors = read_json(ERRORS_PATH) or []

    log_step("Lecture des fichiers CSS/SCSS...")
    file_contents = read_css_files(project_map)

    if not file_contents:
        log_error("Aucun fichier CSS/SCSS trouvé")
        # Write empty result
        result = {
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "source_files": [],
            "animations": [],
            "transitions": [],
            "prefers_reduced_motion": {
                "media_query_present": False,
                "files_with_query": [],
                "animations_covered": 0,
                "animations_not_covered": 0,
            },
            "summary": {
                "total_animations": 0,
                "total_transitions": 0,
                "flagged_count": 0,
                "has_reduced_motion_support": False,
                "infinite_animations_count": 0,
            },
        }
        write_json(OUTPUT_PATH, result)
        log_success("motion-audit.json — aucun fichier CSS trouvé")
        return

    source_files = [f for f, _ in file_contents]
    all_animations = []
    all_transitions = []
    files_with_reduced_motion = []
    all_covered_names = set()

    for file_path, content in file_contents:
        try:
            # --- Find prefers-reduced-motion coverage ---
            if RE_REDUCED_MOTION.search(content):
                files_with_reduced_motion.append(file_path)
                covered = extract_keyframes_names_in_reduced_motion(content)
                all_covered_names.update(covered)

            # --- Find @keyframes ---
            for match in RE_KEYFRAMES.finditer(content):
                kf_name = match.group(1)
                line = find_line_number(content, match.start())

                # Find duration: look for animation properties referencing this keyframe
                duration_ms = 0
                iteration_count = "1"

                # Search for animation shorthand or animation-name that uses this keyframe
                for anim_match in RE_ANIMATION_SHORTHAND.finditer(content):
                    val = anim_match.group(1)
                    if kf_name in val:
                        duration_ms = extract_duration_from_shorthand(val)
                        if 'infinite' in val:
                            iteration_count = "infinite"
                        break

                # Also check animation-duration separately
                if duration_ms == 0:
                    for dur_match in RE_ANIMATION_DURATION.finditer(content):
                        # Check if this is near a reference to our keyframe
                        nearby_start = max(0, dur_match.start() - 500)
                        nearby = content[nearby_start:dur_match.start() + 200]
                        if kf_name in nearby:
                            duration_ms = parse_duration_ms(dur_match.group(1))
                            break

                # Check iteration count
                for iter_match in RE_ANIMATION_ITERATION.finditer(content):
                    nearby_start = max(0, iter_match.start() - 500)
                    nearby = content[nearby_start:iter_match.start() + 200]
                    if kf_name in nearby:
                        iteration_count = iter_match.group(1)
                        break

                # Find selectors using this animation
                used_by = []
                for anim_match in RE_ANIMATION_PROPERTY.finditer(content):
                    if kf_name in anim_match.group(1):
                        selector = get_current_selector(content, anim_match.start())
                        if selector != "unknown":
                            used_by.append(selector)

                # Determine if flagged
                is_covered = kf_name in all_covered_names or '__all__' in all_covered_names
                flagged = duration_ms > 300 and not is_covered

                all_animations.append({
                    "name": kf_name,
                    "file": file_path,
                    "line": line,
                    "duration_ms": duration_ms,
                    "iteration_count": iteration_count,
                    "used_by": used_by,
                    "flagged": flagged,
                })

            # --- Find transitions ---
            for match in RE_TRANSITION.finditer(content):
                val = match.group(1).strip()
                line = find_line_number(content, match.start())
                selector = get_current_selector(content, match.start())

                # Parse transition shorthand: property duration easing delay
                # Handle multiple transitions separated by commas
                parts_list = val.split(',')
                for part in parts_list:
                    part = part.strip()
                    if not part or part == 'none' or part == 'inherit':
                        continue

                    tokens = part.split()
                    prop = tokens[0] if tokens else "all"
                    duration_ms = 0
                    easing = "ease"

                    for token in tokens[1:]:
                        dur = parse_duration_ms(token)
                        if dur > 0 and duration_ms == 0:
                            duration_ms = dur
                        elif token in ('ease', 'ease-in', 'ease-out', 'ease-in-out',
                                       'linear', 'step-start', 'step-end') or token.startswith('cubic-bezier'):
                            easing = token

                    interactive = is_interactive_selector(selector)
                    is_transition_covered = '__transitions_all__' in all_covered_names
                    flagged = duration_ms > 300 and interactive and not is_transition_covered

                    all_transitions.append({
                        "selector": selector,
                        "file": file_path,
                        "line": line,
                        "property": prop,
                        "duration_ms": duration_ms,
                        "easing": easing,
                        "flagged": flagged,
                    })

        except Exception as e:
            msg = f"Erreur parsing {file_path}: {e}"
            log_error(msg)
            log_script_error(errors, "14-motion-audit.py", None, msg)
            continue

    # Count infinite animations
    infinite_count = sum(1 for a in all_animations if a["iteration_count"] == "infinite")

    # Count flagged
    flagged_count = sum(1 for a in all_animations if a["flagged"]) + sum(1 for t in all_transitions if t["flagged"])

    # Reduced motion coverage
    total_motion_items = len(all_animations) + len(all_transitions)
    has_reduced_motion = len(files_with_reduced_motion) > 0

    # Estimate covered vs not covered
    covered_anims = sum(1 for a in all_animations if not a["flagged"]) if has_reduced_motion else 0
    covered_trans = sum(1 for t in all_transitions if not t["flagged"]) if has_reduced_motion else 0
    animations_covered = covered_anims + covered_trans
    animations_not_covered = total_motion_items - animations_covered

    result = {
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "source_files": source_files,
        "animations": all_animations,
        "transitions": all_transitions,
        "prefers_reduced_motion": {
            "media_query_present": has_reduced_motion,
            "files_with_query": files_with_reduced_motion,
            "animations_covered": animations_covered,
            "animations_not_covered": animations_not_covered,
        },
        "summary": {
            "total_animations": len(all_animations),
            "total_transitions": len(all_transitions),
            "flagged_count": flagged_count,
            "has_reduced_motion_support": has_reduced_motion,
            "infinite_animations_count": infinite_count,
        },
    }

    write_json(OUTPUT_PATH, result)

    if errors:
        write_json(ERRORS_PATH, errors)

    log_success(
        f"motion-audit.json — {len(all_animations)} animations, "
        f"{len(all_transitions)} transitions, "
        f"{flagged_count} signalées, "
        f"reduced-motion: {'oui' if has_reduced_motion else 'non'}"
    )


if __name__ == "__main__":
    main()

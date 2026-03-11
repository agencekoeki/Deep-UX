#!/usr/bin/env python3
"""03-build-page-map.py — Construit la carte exhaustive des pages/routes accessibles.

Lit project-map.json et produit page-map.json.

Usage : python3 scripts/03-build-page-map.py
Output : .audit/page-map.json
"""

import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from file_utils import read_json, write_json, ensure_dir
from progress import log_phase, log_step, log_success, log_error, log_skip

AUDIT_DIR = ".audit"
PROJECT_MAP_PATH = os.path.join(AUDIT_DIR, "project-map.json")
OUTPUT_PATH = os.path.join(AUDIT_DIR, "page-map.json")


def is_parameterized(route):
    """Détecte si une route contient des paramètres dynamiques (:id, [slug], etc.)."""
    return bool(re.search(r":[a-zA-Z_]|[\[\{]", route))


def guess_page_type(path_or_url):
    """Devine le type de page d'après son nom."""
    path_lower = path_or_url.lower()
    if any(k in path_lower for k in ["dashboard", "overview", "home"]):
        return "dashboard"
    if any(k in path_lower for k in ["login", "signin", "register", "signup", "auth"]):
        return "form"
    if any(k in path_lower for k in ["form", "edit", "create", "new", "settings", "profile"]):
        return "form"
    if any(k in path_lower for k in ["list", "index", "table", "browse"]):
        return "list"
    if any(k in path_lower for k in ["detail", "view", "show"]):
        return "detail"
    if any(k in path_lower for k in ["landing", "welcome", "hero"]):
        return "landing"
    if any(k in path_lower for k in ["modal", "dialog", "popup"]):
        return "modal"
    return "other"


def guess_requires_auth(path_or_url, file_source=None):
    """Estime si la page nécessite une authentification."""
    path_lower = path_or_url.lower()
    public_patterns = ["login", "signin", "register", "signup", "landing", "home", "index", "about", "contact", "pricing"]
    return not any(p in path_lower for p in public_patterns)


def extract_routes_from_react(project_root, files):
    """Extrait les routes de projets React/Next."""
    pages = []
    page_id = 0

    # Check for Next.js pages/ or app/ directory
    for dir_name in ["pages", "src/pages", "app", "src/app"]:
        pages_dir = os.path.join(project_root, dir_name)
        if os.path.isdir(pages_dir):
            for root, dirs, filenames in os.walk(pages_dir):
                dirs[:] = [d for d in dirs if not d.startswith("_") and not d.startswith(".")]
                for fname in filenames:
                    if fname.startswith("_") or fname.startswith("."):
                        continue
                    if not any(fname.endswith(ext) for ext in [".tsx", ".jsx", ".js", ".ts"]):
                        continue
                    rel = os.path.relpath(os.path.join(root, fname), pages_dir)
                    route = "/" + rel.rsplit(".", 1)[0]
                    route = route.replace("\\", "/")
                    route = re.sub(r"/index$", "", route) or "/"
                    route = re.sub(r"\[([^\]]+)\]", r":\1", route)
                    route = re.sub(r"/page$", "", route) or "/"
                    file_source = os.path.relpath(os.path.join(root, fname), project_root)
                    page_id += 1
                    pages.append({
                        "id": f"page-{page_id:03d}",
                        "url_or_path": route,
                        "file_source": file_source,
                        "requires_auth": guess_requires_auth(route, file_source),
                        "page_type": guess_page_type(route),
                        "parameterized": is_parameterized(route),
                        "screenshot_path": None,
                        "audited": False,
                    })

    # Parse React Router routes if no pages found via file convention
    if not pages:
        route_pattern = re.compile(r'<Route\s+[^>]*path=["\']([^"\']+)["\']', re.IGNORECASE)
        all_source_files = files.get("tsx", []) + files.get("jsx", []) + files.get("js", [])
        for src_file in all_source_files:
            full_path = os.path.join(project_root, src_file)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for match in route_pattern.finditer(content):
                    route = match.group(1)
                    page_id += 1
                    pages.append({
                        "id": f"page-{page_id:03d}",
                        "url_or_path": route,
                        "file_source": src_file,
                        "requires_auth": guess_requires_auth(route),
                        "page_type": guess_page_type(route),
                        "parameterized": is_parameterized(route),
                        "screenshot_path": None,
                        "audited": False,
                    })
            except (OSError, IOError):
                continue

    return pages


def extract_routes_from_vue(project_root, files):
    """Extrait les routes de projets Vue/Nuxt."""
    pages = []
    page_id = 0

    # Nuxt pages/ convention
    for dir_name in ["pages", "src/pages"]:
        pages_dir = os.path.join(project_root, dir_name)
        if os.path.isdir(pages_dir):
            for root, dirs, filenames in os.walk(pages_dir):
                for fname in filenames:
                    if not fname.endswith(".vue"):
                        continue
                    rel = os.path.relpath(os.path.join(root, fname), pages_dir)
                    route = "/" + rel.rsplit(".", 1)[0]
                    route = route.replace("\\", "/")
                    route = re.sub(r"/index$", "", route) or "/"
                    file_source = os.path.relpath(os.path.join(root, fname), project_root)
                    page_id += 1
                    pages.append({
                        "id": f"page-{page_id:03d}",
                        "url_or_path": route,
                        "file_source": file_source,
                        "requires_auth": guess_requires_auth(route),
                        "page_type": guess_page_type(route),
                        "parameterized": is_parameterized(route),
                        "screenshot_path": None,
                        "audited": False,
                    })

    # Vue Router
    if not pages:
        route_pattern = re.compile(r"path:\s*['\"]([^'\"]+)['\"]")
        router_candidates = ["src/router/index.js", "src/router/index.ts", "src/router.js", "src/router.ts"]
        for candidate in router_candidates:
            full_path = os.path.join(project_root, candidate)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    for match in route_pattern.finditer(content):
                        route = match.group(1)
                        page_id += 1
                        pages.append({
                            "id": f"page-{page_id:03d}",
                            "url_or_path": route,
                            "file_source": candidate,
                            "requires_auth": guess_requires_auth(route),
                            "page_type": guess_page_type(route),
                            "parameterized": is_parameterized(route),
                            "screenshot_path": None,
                            "audited": False,
                        })
                except (OSError, IOError):
                    continue

    return pages


def extract_pages_static(project_root, files):
    """Extrait les pages pour les projets HTML statiques."""
    pages = []
    page_id = 0
    for html_file in files.get("html", []):
        route = "/" + html_file.replace("\\", "/")
        if route.endswith("/index.html"):
            route = route[:-len("index.html")] or "/"
        page_id += 1
        pages.append({
            "id": f"page-{page_id:03d}",
            "url_or_path": route,
            "file_source": html_file,
            "requires_auth": False,
            "page_type": guess_page_type(html_file),
            "parameterized": is_parameterized(route),
            "screenshot_path": None,
            "audited": False,
        })
    return pages


def extract_pages_php(project_root, files):
    """Extrait les pages pour les projets PHP."""
    pages = []
    page_id = 0
    for php_file in files.get("php", []):
        if any(skip in php_file.lower() for skip in ["vendor/", "config/", "migration", "seed", "test"]):
            continue
        route = "/" + php_file.replace("\\", "/")
        page_id += 1
        pages.append({
            "id": f"page-{page_id:03d}",
            "url_or_path": route,
            "file_source": php_file,
            "requires_auth": guess_requires_auth(php_file),
            "page_type": guess_page_type(php_file),
            "parameterized": is_parameterized(route),
            "screenshot_path": None,
            "audited": False,
        })
    return pages


def deduplicate_pages(pages):
    """Supprime les doublons par url_or_path."""
    seen = set()
    unique = []
    for page in pages:
        if page["url_or_path"] not in seen:
            seen.add(page["url_or_path"])
            unique.append(page)
    return unique


def main():
    log_phase(1, "Build Page Map", inputs=[PROJECT_MAP_PATH], outputs=[OUTPUT_PATH])

    project_map = read_json(PROJECT_MAP_PATH)
    if not project_map:
        log_error(f"{PROJECT_MAP_PATH} introuvable — lancez d'abord 02-discover.py")
        sys.exit(1)

    # Check existing
    existing = read_json(OUTPUT_PATH)
    if existing and existing.get("pages"):
        log_skip("page-map.json déjà existant")
        return

    stack = project_map.get("stack", {})
    files = project_map.get("files", {})
    project_root = project_map.get("project_root", os.getcwd())

    log_step(f"Stack détecté : {stack.get('type', 'unknown')}")

    stack_type = stack.get("type", "unknown")
    if stack_type == "react":
        pages = extract_routes_from_react(project_root, files)
    elif stack_type == "vue":
        pages = extract_routes_from_vue(project_root, files)
    elif stack_type == "static":
        pages = extract_pages_static(project_root, files)
    elif stack_type == "php":
        pages = extract_pages_php(project_root, files)
    else:
        # Fallback : mix static + any detected
        pages = extract_pages_static(project_root, files)
        pages.extend(extract_pages_php(project_root, files))

    pages = deduplicate_pages(pages)
    auth_count = sum(1 for p in pages if p["requires_auth"])

    page_map = {
        "pages": pages,
        "total_pages": len(pages),
        "auth_required_count": auth_count,
    }

    write_json(OUTPUT_PATH, page_map)
    log_success(f"{len(pages)} pages trouvées ({auth_count} nécessitent auth)")
    log_success(f"Écrit : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

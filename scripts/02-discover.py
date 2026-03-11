#!/usr/bin/env python3
"""02-discover.py — Analyse le projet cible et produit une cartographie complète.

Ne modifie JAMAIS les fichiers du projet cible — lecture seule absolue.

Usage : python3 scripts/02-discover.py [chemin_du_projet]
Output : .audit/project-map.json
"""

import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from file_utils import read_json, write_json, ensure_dir
from progress import log_phase, log_step, log_success, log_error, log_skip

AUDIT_DIR = ".audit"
OUTPUT_PATH = os.path.join(AUDIT_DIR, "project-map.json")

FILE_EXTENSIONS = {
    "html": [".html", ".htm"],
    "css": [".css"],
    "scss": [".scss", ".sass"],
    "js": [".js", ".mjs"],
    "jsx": [".jsx"],
    "ts": [".ts"],
    "tsx": [".tsx"],
    "vue": [".vue"],
    "php": [".php"],
    "py": [".py"],
}

IGNORE_DIRS = {
    "node_modules", ".git", ".audit", "__pycache__", "vendor",
    "dist", "build", ".next", ".nuxt", ".output", "coverage",
    ".cache", ".parcel-cache", "bower_components",
}


def count_lines(filepath):
    """Compte les lignes d'un fichier."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except (OSError, IOError):
        return 0


def scan_files(project_root):
    """Inventorie tous les fichiers par type."""
    files = {ext_type: [] for ext_type in FILE_EXTENSIONS}
    loc = {ext_type: 0 for ext_type in FILE_EXTENSIONS}

    for root, dirs, filenames in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fname in filenames:
            filepath = os.path.join(root, fname)
            relpath = os.path.relpath(filepath, project_root)
            _, ext = os.path.splitext(fname)
            ext = ext.lower()
            for ext_type, extensions in FILE_EXTENSIONS.items():
                if ext in extensions:
                    files[ext_type].append(relpath)
                    loc[ext_type] += count_lines(filepath)
                    break

    total = sum(len(v) for v in files.values())
    files["total_count"] = total
    return files, loc


def detect_stack(project_root, files):
    """Détecte le type de projet, framework, UI library et router."""
    stack = {
        "type": "unknown",
        "framework": "unknown",
        "ui_library": "unknown",
        "router": "unknown",
    }

    pkg_path = os.path.join(project_root, "package.json")
    composer_path = os.path.join(project_root, "composer.json")
    pkg = None

    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg = json.load(f)
        except (json.JSONDecodeError, OSError):
            pkg = {}

    deps_all = {}
    if pkg:
        deps_all.update(pkg.get("dependencies", {}))
        deps_all.update(pkg.get("devDependencies", {}))

    # Detect type
    if files.get("tsx") or files.get("jsx") or "react" in deps_all:
        stack["type"] = "react"
    elif files.get("vue") or "vue" in deps_all:
        stack["type"] = "vue"
    elif "@angular/core" in deps_all:
        stack["type"] = "angular"
    elif os.path.exists(composer_path) or files.get("php"):
        stack["type"] = "php"
    elif files.get("html"):
        stack["type"] = "static"

    # Detect framework
    if "next" in deps_all:
        stack["framework"] = "next"
    elif "nuxt" in deps_all or "nuxt3" in deps_all:
        stack["framework"] = "nuxt"
    elif os.path.exists(composer_path):
        try:
            with open(composer_path, "r", encoding="utf-8") as f:
                composer = json.load(f)
            composer_deps = composer.get("require", {})
            if "laravel/framework" in composer_deps:
                stack["framework"] = "laravel"
            elif any("wordpress" in k for k in composer_deps):
                stack["framework"] = "wordpress"
        except (json.JSONDecodeError, OSError):
            pass
    if stack["framework"] == "unknown":
        if os.path.exists(os.path.join(project_root, "wp-config.php")) or os.path.exists(
            os.path.join(project_root, "wp-content")
        ):
            stack["framework"] = "wordpress"
        elif stack["type"] != "unknown":
            stack["framework"] = "none"

    # Detect UI library
    if "tailwindcss" in deps_all:
        stack["ui_library"] = "tailwind"
    elif "bootstrap" in deps_all or "react-bootstrap" in deps_all:
        stack["ui_library"] = "bootstrap"
    elif "@mui/material" in deps_all or "@material-ui/core" in deps_all:
        stack["ui_library"] = "mui"
    elif "antd" in deps_all:
        stack["ui_library"] = "antd"
    else:
        stack["ui_library"] = "none"

    # Detect router
    if "react-router-dom" in deps_all or "react-router" in deps_all:
        stack["router"] = "react-router"
    elif "vue-router" in deps_all:
        stack["router"] = "vue-router"
    elif stack["framework"] == "next":
        stack["router"] = "next"
    else:
        stack["router"] = "none"

    return stack, deps_all


def find_entry_points(project_root, stack, files):
    """Identifie les points d'entrée."""
    entries = []
    candidates = [
        "index.html", "src/index.html", "public/index.html",
        "src/App.tsx", "src/App.jsx", "src/App.vue", "src/main.tsx",
        "src/main.ts", "src/main.js", "src/index.tsx", "src/index.jsx",
        "src/index.js", "index.php", "public/index.php",
        "pages/index.tsx", "pages/index.jsx", "pages/index.vue",
        "app/page.tsx", "app/page.jsx",
    ]
    for candidate in candidates:
        if os.path.exists(os.path.join(project_root, candidate)):
            entries.append(candidate)
    return entries


def find_config_files(project_root):
    """Identifie les fichiers de configuration."""
    configs = []
    candidates = [
        "package.json", "tsconfig.json", "tailwind.config.js", "tailwind.config.ts",
        "vite.config.js", "vite.config.ts", "next.config.js", "next.config.mjs",
        "nuxt.config.ts", "nuxt.config.js", "webpack.config.js",
        ".eslintrc.json", ".eslintrc.js", ".prettierrc",
        "composer.json", ".env.example", "postcss.config.js",
        "angular.json", "vue.config.js",
    ]
    for candidate in candidates:
        if os.path.exists(os.path.join(project_root, candidate)):
            configs.append(candidate)
    return configs


def format_dependencies(deps_all, stack):
    """Formate les dépendances UI majeures détectées."""
    detected = []
    notable = {
        "bootstrap": "Bootstrap", "tailwindcss": "Tailwind CSS",
        "@mui/material": "MUI", "antd": "Ant Design",
        "react": "React", "vue": "Vue", "next": "Next.js",
        "nuxt": "Nuxt", "@angular/core": "Angular",
        "styled-components": "styled-components", "emotion": "Emotion",
        "sass": "Sass", "less": "Less",
        "axios": "Axios", "react-query": "React Query",
        "@tanstack/react-query": "TanStack Query",
        "redux": "Redux", "@reduxjs/toolkit": "Redux Toolkit",
        "zustand": "Zustand", "pinia": "Pinia", "vuex": "Vuex",
        "framer-motion": "Framer Motion", "gsap": "GSAP",
    }
    for dep, label in notable.items():
        if dep in deps_all:
            version = deps_all[dep]
            if isinstance(version, str):
                detected.append(f"{label} {version}")
            else:
                detected.append(label)
    return detected


def main():
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    project_root = os.path.abspath(project_root)

    log_phase(1, "Discovery", inputs=[project_root], outputs=[OUTPUT_PATH])

    # Check if already done
    existing = read_json(OUTPUT_PATH)
    if existing and existing.get("project_root") == project_root:
        log_skip("project-map.json déjà existant pour ce projet")
        return

    ensure_dir(AUDIT_DIR)

    log_step("Scan des fichiers...")
    files, loc = scan_files(project_root)
    log_success(f"{files['total_count']} fichiers trouvés")

    log_step("Détection du stack...")
    stack, deps_all = detect_stack(project_root, files)
    log_success(f"Stack : {stack['type']} / {stack['framework']} / {stack['ui_library']}")

    log_step("Identification des points d'entrée...")
    entry_points = find_entry_points(project_root, stack, files)
    log_success(f"{len(entry_points)} point(s) d'entrée")

    log_step("Identification des fichiers de configuration...")
    config_files = find_config_files(project_root)
    log_success(f"{len(config_files)} fichier(s) de configuration")

    log_step("Détection des dépendances UI...")
    dependencies = format_dependencies(deps_all, stack)
    log_success(f"{len(dependencies)} dépendance(s) notable(s)")

    project_map = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "project_root": project_root,
        "stack": stack,
        "files": files,
        "entry_points": entry_points,
        "config_files": config_files,
        "dependencies_detected": dependencies,
        "loc_by_type": loc,
    }

    write_json(OUTPUT_PATH, project_map)
    log_success(f"Écrit : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

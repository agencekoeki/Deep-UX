#!/usr/bin/env python3
"""00b-estimate-run.py — Estimateur de coût et durée avant lancement de l'audit.

Lit le page-map (ou lance une découverte rapide) et estime :
- Nombre d'agents à lancer
- Tokens estimés
- Durée approximative
- Coût estimé

Usage : python3 scripts/00b-estimate-run.py [chemin_projet]
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from file_utils import read_json, write_json, ensure_dir
from auth import load_env
from progress import log_phase, log_step, log_success, log_error

AUDIT_DIR = ".audit"

# Ratios conservatifs (tokens)
TOKENS_PER_PAGE_PER_DISCIPLINE = 3000
TOKENS_FIXED_AGENTS = 15000
TOKENS_REPORT = 5000
DISCIPLINES_COUNT = 5
FIXED_AGENTS_COUNT = 17

# Coût par million de tokens (Opus 4.6 estimate, input+output blend)
COST_PER_MILLION_TOKENS = 4.0

# Durée estimée par agent (secondes)
SECONDS_PER_AGENT = 20


def estimate(project_root="."):
    log_phase("0b", "Estimation du run", outputs=[f"{AUDIT_DIR}/run-estimate.json"])
    ensure_dir(AUDIT_DIR)

    env = load_env()
    roles_count = int(env.get("AUTH_ROLES_COUNT", "1"))

    # Try to read existing page-map
    page_map = read_json(os.path.join(AUDIT_DIR, "page-map.json"))
    if page_map and "pages" in page_map:
        pages_count = len(page_map["pages"])
        log_step(f"page-map.json trouvé : {pages_count} pages")
    else:
        # Quick estimation from project-map
        project_map = read_json(os.path.join(AUDIT_DIR, "project-map.json"))
        if project_map and "files" in project_map:
            html_count = len(project_map["files"].get("html", []))
            tsx_count = len(project_map["files"].get("tsx", []))
            jsx_count = len(project_map["files"].get("jsx", []))
            vue_count = len(project_map["files"].get("vue", []))
            php_count = len(project_map["files"].get("php", []))
            pages_count = max(html_count + tsx_count + jsx_count + vue_count + php_count, 1)
            log_step(f"Estimation depuis project-map.json : ~{pages_count} pages potentielles")
        else:
            log_error("Aucun page-map.json ni project-map.json trouvé.")
            log_step("Lancez d'abord : python3 scripts/02-discover.py && python3 scripts/03-build-page-map.py")
            pages_count = 0

    # Calculate
    total_audits = pages_count * roles_count
    discipline_agents = total_audits * DISCIPLINES_COUNT
    total_agents = discipline_agents + FIXED_AGENTS_COUNT
    tokens_disciplines = total_audits * DISCIPLINES_COUNT * TOKENS_PER_PAGE_PER_DISCIPLINE
    tokens_total = tokens_disciplines + TOKENS_FIXED_AGENTS + TOKENS_REPORT
    duration_seconds = total_agents * SECONDS_PER_AGENT
    duration_min = duration_seconds / 60
    duration_max = duration_min * 2  # conservative upper bound
    cost_low = (tokens_total / 1_000_000) * COST_PER_MILLION_TOKENS * 0.8
    cost_high = (tokens_total / 1_000_000) * COST_PER_MILLION_TOKENS * 1.5

    # Output
    estimate_data = {
        "pages_detected": pages_count,
        "roles_count": roles_count,
        "total_audits": total_audits,
        "agents_to_launch": total_agents,
        "tokens_estimated": tokens_total,
        "duration_min_minutes": round(duration_min),
        "duration_max_minutes": round(duration_max),
        "cost_low_usd": round(cost_low, 2),
        "cost_high_usd": round(cost_high, 2),
    }

    write_json(os.path.join(AUDIT_DIR, "run-estimate.json"), estimate_data)

    # Display
    print()
    print("━" * 50)
    print("  deep-ux — Estimation du run")
    print("━" * 50)
    print(f"  Pages détectées      : {pages_count}")
    print(f"  Rôles à auditer      : {roles_count}")
    print(f"  Agents à lancer      : ~{total_agents} ({DISCIPLINES_COUNT} disciplines × {total_audits} pages + {FIXED_AGENTS_COUNT} fixes)")
    print(f"  Tokens estimés       : ~{tokens_total:,}")
    print(f"  Durée estimée        : ~{round(duration_min)}-{round(duration_max)} minutes")
    print(f"  Coût estimé          : ~${cost_low:.2f}-{cost_high:.2f} (Opus 4.6)")
    print("━" * 50)

    dry_run = env.get("DRY_RUN", "false").lower() == "true"
    if dry_run:
        print("  Mode DRY_RUN activé — l'audit ne sera pas lancé.")
        print("  Pour lancer le run complet : DRY_RUN=false dans .env")
    else:
        print("  Pour réduire le périmètre : ajoutez des URLs dans EXCLUDE_URLS")
    print("━" * 50)
    print()

    log_success(f"Estimation sauvegardée dans {AUDIT_DIR}/run-estimate.json")
    return estimate_data


if __name__ == "__main__":
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    os.chdir(project_root)
    estimate(project_root)

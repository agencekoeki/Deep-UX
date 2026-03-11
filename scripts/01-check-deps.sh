#!/usr/bin/env bash
# 01-check-deps.sh — Vérifie que toutes les dépendances sont installées.
# Retourne exit 0 si tout ok, exit 1 avec message clair sinon.
# N'installe JAMAIS automatiquement.

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  deep-ux — Vérification des dépendances"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

errors=0

# Python 3.8+
if command -v python3 &>/dev/null; then
    py_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    py_major=$(echo "$py_version" | cut -d. -f1)
    py_minor=$(echo "$py_version" | cut -d. -f2)
    if [ "$py_major" -ge 3 ] && [ "$py_minor" -ge 8 ]; then
        echo "  ✓ Python $py_version"
    else
        echo "  ✗ Python $py_version détecté — version 3.8+ requise"
        errors=$((errors + 1))
    fi
else
    echo "  ✗ Python 3 non trouvé"
    echo "    → Installer : https://www.python.org/downloads/"
    errors=$((errors + 1))
fi

# pip
if command -v pip3 &>/dev/null; then
    pip_version=$(pip3 --version 2>/dev/null | head -1)
    echo "  ✓ pip ($pip_version)"
else
    echo "  ✗ pip3 non trouvé"
    echo "    → Installer : python3 -m ensurepip --upgrade"
    errors=$((errors + 1))
fi

# Playwright
if python3 -c "import playwright" 2>/dev/null; then
    echo "  ✓ playwright (module Python)"
else
    echo "  ✗ playwright non installé"
    echo "    → Installer : pip3 install playwright"
    errors=$((errors + 1))
fi

# Chromium pour Playwright
if command -v playwright &>/dev/null; then
    if playwright install --dry-run chromium &>/dev/null 2>&1; then
        echo "  ✓ chromium (Playwright)"
    else
        echo "  ⚠ chromium Playwright — statut incertain"
        echo "    → Installer si nécessaire : playwright install chromium"
    fi
else
    if python3 -m playwright install --dry-run chromium &>/dev/null 2>&1; then
        echo "  ✓ chromium (Playwright via python3 -m)"
    else
        echo "  ⚠ chromium Playwright — impossible de vérifier"
        echo "    → Installer : python3 -m playwright install chromium"
    fi
fi

# Librairies Python
python_libs=("cssutils" "bs4:beautifulsoup4" "requests" "json")
for lib_entry in "${python_libs[@]}"; do
    import_name="${lib_entry%%:*}"
    install_name="${lib_entry##*:}"
    if python3 -c "import $import_name" 2>/dev/null; then
        echo "  ✓ $install_name"
    else
        echo "  ✗ $install_name non installé"
        echo "    → Installer : pip3 install $install_name"
        if [ "$import_name" != "json" ]; then
            errors=$((errors + 1))
        fi
    fi
done

# Dépendances v4 — scripts de mesure
echo ""
echo "  — Dépendances v4 (scripts de mesure) —"

# axe-core — injecté via CDN, pas de dépendance locale
echo "  ✓ axe-core — injecté via CDN (pas d'installation locale requise)"

# Pillow (pour contrast-real.py)
if python3 -c "import PIL" 2>/dev/null; then
    echo "  ✓ Pillow"
else
    echo "  ⚠ Pillow manquant (requis pour 13-contrast-real.py)"
    echo "    → Installer : pip install Pillow --break-system-packages"
    echo "    Note : non bloquant — contrast-real.py sera skippé si absent"
fi

# pyphen (pour 10-readability.py)
if python3 -c "import pyphen" 2>/dev/null; then
    echo "  ✓ pyphen"
else
    echo "  ⚠ pyphen manquant (requis pour 10-readability.py)"
    echo "    → Installer : pip install pyphen --break-system-packages"
    echo "    Note : non bloquant — readability.py utilisera une estimation syllabique simplifiée"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$errors" -gt 0 ]; then
    echo "  $errors dépendance(s) manquante(s) — corrigez avant de continuer"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
else
    echo "  Toutes les dépendances sont installées ✓"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
fi

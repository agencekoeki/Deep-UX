#!/usr/bin/env bash
# 00-bootstrap.sh — Prépare l'environnement de travail .audit/
# Idempotent : peut être relancé sans écraser ce qui existe.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
AUDIT_DIR=".audit"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  deep-ux — Bootstrap"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Créer le dossier .audit/ et ses sous-dossiers
SUBDIRS=("screenshots" "screen-audits" "phase2" "phase4" "reports" "quality-gates" "archives")
created=0

if [ ! -d "$AUDIT_DIR" ]; then
    mkdir -p "$AUDIT_DIR"
    echo "  ✓ Créé : $AUDIT_DIR/"
    created=$((created + 1))
else
    echo "  ⊘ Existe déjà : $AUDIT_DIR/"
fi

for subdir in "${SUBDIRS[@]}"; do
    if [ ! -d "$AUDIT_DIR/$subdir" ]; then
        mkdir -p "$AUDIT_DIR/$subdir"
        echo "  ✓ Créé : $AUDIT_DIR/$subdir/"
        created=$((created + 1))
    else
        echo "  ⊘ Existe déjà : $AUDIT_DIR/$subdir/"
    fi
done

# 2. Copier .gitignore du template
if [ -f "$PLUGIN_ROOT/.audit-template/.gitignore" ]; then
    if [ ! -f "$AUDIT_DIR/.gitignore" ]; then
        cp "$PLUGIN_ROOT/.audit-template/.gitignore" "$AUDIT_DIR/.gitignore"
        echo "  ✓ Copié : .audit-template/.gitignore → $AUDIT_DIR/.gitignore"
        created=$((created + 1))
    else
        echo "  ⊘ Existe déjà : $AUDIT_DIR/.gitignore"
    fi
fi

# 3. Copier .env.example → .env si .env n'existe pas
if [ ! -f "$AUDIT_DIR/.env" ]; then
    if [ -f "$PLUGIN_ROOT/.audit-template/.env.example" ]; then
        cp "$PLUGIN_ROOT/.audit-template/.env.example" "$AUDIT_DIR/.env"
        echo "  ✓ Copié : .audit-template/.env.example → $AUDIT_DIR/.env"
        created=$((created + 1))
    fi
else
    echo "  ⊘ Existe déjà : $AUDIT_DIR/.env"
fi

# 4. Vérifier que .audit/ est dans le .gitignore du projet cible
if [ -f ".gitignore" ]; then
    if ! grep -q "^\.audit/" ".gitignore" 2>/dev/null; then
        echo ".audit/" >> ".gitignore"
        echo "  ✓ Ajouté .audit/ au .gitignore du projet"
        created=$((created + 1))
    else
        echo "  ⊘ .audit/ déjà dans .gitignore"
    fi
else
    echo ".audit/" > ".gitignore"
    echo "  ✓ Créé .gitignore avec .audit/"
    created=$((created + 1))
fi

# 5. Résumé
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Bootstrap terminé — $created éléments créés"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Prochaine étape : configurer $AUDIT_DIR/.env"

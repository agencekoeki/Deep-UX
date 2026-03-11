"""Module d'affichage de progression terminal."""

import sys


def log_phase(n, title, inputs=None, outputs=None):
    """Affiche l'entête de phase."""
    print(f"\n{'━' * 50}")
    print(f"  Phase {n} — {title}")
    print(f"{'━' * 50}")
    if inputs:
        print(f"  Inputs  : {', '.join(inputs)}")
    if outputs:
        print(f"  Outputs : {', '.join(outputs)}")
    print()


def log_step(message):
    """Affiche une étape en cours."""
    print(f"  → {message}")
    sys.stdout.flush()


def log_success(message):
    """Affiche un succès."""
    print(f"  ✓ {message}")
    sys.stdout.flush()


def log_error(message):
    """Affiche une erreur."""
    print(f"  ✗ {message}", file=sys.stderr)
    sys.stderr.flush()


def log_skip(message):
    """Affiche un skip (fichier déjà produit)."""
    print(f"  ⊘ {message} (déjà existant, skip)")
    sys.stdout.flush()

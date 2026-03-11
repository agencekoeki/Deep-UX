"""Module utilitaires fichiers — lecture/écriture JSON, gestion de dossiers."""

import os
import re
import json


def read_json(path):
    """Lit un fichier JSON, retourne None si absent."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    """Écrit un JSON formaté avec indentation (écriture atomique via .tmp + rename)."""
    ensure_dir(os.path.dirname(path))
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def ensure_dir(path):
    """Crée le dossier si absent."""
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def slugify(text):
    """Transforme une URL ou un texte en nom de fichier valide."""
    text = text.strip("/").replace("/", "-").replace("\\", "-")
    text = re.sub(r"[^a-zA-Z0-9\-_]", "-", text)
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text or "index"

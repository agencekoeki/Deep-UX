"""Module auth partagé — gestion de l'authentification et des credentials."""

import os
import json


AUDIT_DIR = os.path.join(os.getcwd(), ".audit")
ENV_PATH = os.path.join(AUDIT_DIR, ".env")
AUTH_STATE_PATH = os.path.join(AUDIT_DIR, "auth-state.json")


def load_env():
    """Lit .audit/.env et retourne un dict clé=valeur."""
    env = {}
    if not os.path.exists(ENV_PATH):
        return env
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def get_auth_config():
    """Retourne la configuration d'authentification depuis .env."""
    env = load_env()
    return {
        "base_url": env.get("BASE_URL", "http://localhost:3000"),
        "auth_type": env.get("AUTH_TYPE", "none"),
        "login_url": env.get("AUTH_LOGIN_URL", "/login"),
        "username": env.get("AUTH_USERNAME", ""),
        "password": env.get("AUTH_PASSWORD", ""),
        "success_url": env.get("AUTH_SUCCESS_URL", "/dashboard"),
        "viewport_width": int(env.get("SCREENSHOT_VIEWPORT_WIDTH", "1440")),
        "viewport_height": int(env.get("SCREENSHOT_VIEWPORT_HEIGHT", "900")),
        "exclude_urls": [u.strip() for u in env.get("EXCLUDE_URLS", "").split(",") if u.strip()],
        "screenshot_mobile": env.get("SCREENSHOT_MOBILE", "false").lower() == "true",
        "screenshot_mobile_width": int(env.get("SCREENSHOT_MOBILE_WIDTH", "375")),
        "screenshot_delay_ms": int(env.get("SCREENSHOT_DELAY_MS", "0")),
        "playwright_timeout_ms": int(env.get("PLAYWRIGHT_TIMEOUT_MS", "30000")),
    }


def load_auth_state():
    """Charge .audit/auth-state.json — retourne None si absent."""
    if not os.path.exists(AUTH_STATE_PATH):
        return None
    with open(AUTH_STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_auth_state(state):
    """Sauvegarde le storage state Playwright dans .audit/auth-state.json."""
    with open(AUTH_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

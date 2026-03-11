#!/usr/bin/env python3
"""06-export-session-helper.py — Guide interactif pour exporter une session browser (auth SSO).

Lance un petit serveur local temporaire qui attend le fichier exporté,
valide le format et le sauvegarde dans .audit/auth-state.json.

Usage : python3 scripts/06-export-session-helper.py
"""

import os
import sys
import json
import http.server
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from file_utils import ensure_dir
from auth import save_auth_state, AUTH_STATE_PATH
from progress import log_phase, log_step, log_success, log_error

AUDIT_DIR = ".audit"
PORT = 9222


HTML_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>deep-ux — Export Session</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 700px; margin: 40px auto; padding: 20px; background: #f9fafb; color: #1f2937; }
        h1 { color: #111827; }
        .step { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 12px 0; }
        .step h3 { margin-top: 0; color: #4f46e5; }
        textarea { width: 100%; height: 200px; font-family: monospace; font-size: 13px; border: 2px solid #d1d5db; border-radius: 6px; padding: 12px; }
        button { background: #4f46e5; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 12px; }
        button:hover { background: #4338ca; }
        .success { background: #d1fae5; border-color: #34d399; color: #065f46; padding: 16px; border-radius: 8px; display: none; }
        .error { background: #fee2e2; border-color: #f87171; color: #991b1b; padding: 16px; border-radius: 8px; display: none; }
        code { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
    </style>
</head>
<body>
    <h1>deep-ux — Export de session</h1>
    <p>Ce guide vous aide à exporter votre session browser pour les pages nécessitant une authentification SSO.</p>

    <div class="step">
        <h3>Étape 1 — Ouvrir la console du navigateur</h3>
        <p>Connectez-vous à votre application dans Chrome/Edge, puis ouvrez la console (F12 → Console).</p>
    </div>

    <div class="step">
        <h3>Étape 2 — Copier le storage state</h3>
        <p>Collez ce code dans la console et exécutez-le :</p>
        <code>
        JSON.stringify({cookies: document.cookie.split(';').map(c => {let [n,...v] = c.trim().split('='); return {name:n, value:v.join('='), domain:location.hostname, path:'/'}}), origins: [{origin: location.origin, localStorage: Object.entries(localStorage).map(([k,v])=>({name:k,value:v}))}]})
        </code>
    </div>

    <div class="step">
        <h3>Étape 3 — Coller le résultat ici</h3>
        <textarea id="stateInput" placeholder="Collez le JSON ici..."></textarea>
        <br>
        <button onclick="submitState()">Envoyer</button>
    </div>

    <div class="success" id="success">Session exportée avec succès ! Vous pouvez fermer cette page.</div>
    <div class="error" id="error"></div>

    <script>
    async function submitState() {
        const input = document.getElementById('stateInput').value.trim();
        const successEl = document.getElementById('success');
        const errorEl = document.getElementById('error');
        successEl.style.display = 'none';
        errorEl.style.display = 'none';

        try {
            const parsed = JSON.parse(input);
            const resp = await fetch('/save-state', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(parsed)
            });
            if (resp.ok) {
                successEl.style.display = 'block';
            } else {
                const text = await resp.text();
                errorEl.textContent = 'Erreur : ' + text;
                errorEl.style.display = 'block';
            }
        } catch(e) {
            errorEl.textContent = 'JSON invalide : ' + e.message;
            errorEl.style.display = 'block';
        }
    }
    </script>
</body>
</html>"""


class SessionHandler(http.server.BaseHTTPRequestHandler):
    """Serveur HTTP pour recevoir le storage state."""

    received = False

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        if self.path == "/save-state":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                state = json.loads(body)
                # Validate minimum structure
                if "cookies" not in state and "origins" not in state:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Format invalide : 'cookies' ou 'origins' requis")
                    return

                save_auth_state(state)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
                SessionHandler.received = True
                log_success(f"Session sauvegardée dans {AUTH_STATE_PATH}")
            except json.JSONDecodeError as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f"JSON invalide : {e}".encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Silence HTTP logs


def main():
    log_phase(0, "Export Session Helper", outputs=[AUTH_STATE_PATH])
    ensure_dir(AUDIT_DIR)

    log_step(f"Démarrage du serveur sur http://localhost:{PORT}")
    print(f"\n  Ouvrez http://localhost:{PORT} dans votre navigateur")
    print("  et suivez les instructions.\n")
    print("  Appuyez sur Ctrl+C pour arrêter.\n")

    server = http.server.HTTPServer(("localhost", PORT), SessionHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        if SessionHandler.received:
            log_success("Serveur arrêté — session exportée")
        else:
            log_error("Serveur arrêté — aucune session reçue")


if __name__ == "__main__":
    main()

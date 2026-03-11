# Agent 16 — Coverage Auditor

## Rôle
Tu produis un rapport honnête de ce que l'audit a couvert et ce qu'il a probablement manqué. Tu tournes après les screenshots (fin Phase 1), avant les audits d'écrans (Phase 3).

## Pré-requis
Avant de commencer, lis :
- `docs/anti-drift-rules.md`
- `.audit/project-map.json`
- `.audit/page-map.json`
- `.audit/.env`

## Inputs
- `.audit/project-map.json`
- `.audit/page-map.json`
- `.audit/.env` (pour AUTH_ROLES_COUNT, SCREENSHOT_MOBILE, etc.)
- Code source du projet (lecture seule)

## Output
`.audit/coverage-report.json`

---

## Ce que tu analyses

### 1. Routes paramétrées
Détecte dans `project-map.json` et le code source les routes de type `/user/:id`, `/product/{slug}`, `/order/[orderId]`.
Signale qu'une seule instance a été capturée pour chaque route paramétrée.

### 2. États vides
Cherche dans le code des composants les patterns :
- `if (items.length === 0)`, `if (!data)`, `items?.length === 0`
- Classes/composants nommés `EmptyState`, `NoData`, `empty-state`
- Textes comme "Aucun résultat", "No data", "Rien à afficher"
Signale les écrans qui ont potentiellement un état vide non capturé.

### 3. États d'erreur
Cherche les patterns :
- `catch`, `error`, `Error`, `ErrorBoundary`
- Pages 404, 500, composants d'erreur
- Messages d'erreur dans le JSX/HTML

### 4. États de chargement
Cherche les patterns :
- `loading`, `isLoading`, `Skeleton`, `Spinner`, `Loader`
- Classes CSS contenant `loading`, `skeleton`

### 5. Rôles multiples
Si `AUTH_ROLES_COUNT > 1` dans `.env` :
- Liste les rôles définis dans `AUTH_ROLES`
- Compare avec les rôles détectés dans le code (guards, middlewares, permissions)
- Signale quels rôles ont été audités vs manquants

### 6. Viewports
Si `SCREENSHOT_MOBILE=false` dans `.env` :
- Signale que la version mobile n'a pas été capturée
- Détecte si le code contient des breakpoints ou des media queries (indiquant un design responsive)

### 7. Pages derrière confirmation
Détecte dans le code la présence de :
- Modals : `Modal`, `Dialog`, `Drawer`, `Popover`, `Overlay`
- Composants de confirmation : `ConfirmDialog`, `AlertDialog`
- Patterns : `confirm(`, `window.confirm`
Signale que ces éléments n'ont probablement pas été capturés en screenshot.

---

## Structure de l'output

```json
{
  "generated_at": "ISO timestamp",
  "coverage_score": 72,
  "pages_captured": 24,
  "pages_estimated_total": 24,
  "uncovered": {
    "parameterized_routes": [
      {"route": "/user/:id", "note": "Capturé avec l'ID de test uniquement"}
    ],
    "empty_states": [
      {"component": "UserList.tsx", "screen": "/users", "evidence": "ligne 45 — empty state JSX détecté"}
    ],
    "error_states": [],
    "loading_states": [
      {"component": "Dashboard.tsx", "screen": "/dashboard"}
    ],
    "missing_roles": ["admin"],
    "missing_viewports": ["mobile"],
    "modal_dialogs": [
      {"name": "DeleteConfirmModal", "triggered_by": "/users"}
    ]
  },
  "manual_audit_checklist": [
    "Auditer l'état vide de /users (aucun utilisateur)",
    "Auditer la vue admin (credentials admin non fournis)",
    "Auditer le modal de confirmation de suppression sur /users",
    "Auditer la version mobile (SCREENSHOT_MOBILE=false)"
  ]
}
```

## Calcul du coverage_score
```
score = 100
score -= 5 par route paramétrée non variée
score -= 5 par état vide non capturé
score -= 3 par état d'erreur non capturé
score -= 2 par état de chargement non capturé
score -= 10 par rôle manquant
score -= 15 si mobile non capturé et responsive détecté
score -= 3 par modal/dialog non capturé
score = max(0, score)
```

## Anti-drift
- Lecture seule absolue sur le code source
- Chaque élément de `uncovered` cite le fichier source et la ligne comme evidence
- Le `manual_audit_checklist` est une liste actionnable, pas des généralités
- Non bloquant : l'audit continue même si la couverture est partielle

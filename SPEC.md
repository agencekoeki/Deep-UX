# SPEC.md — deep-ux
## Document de spécification exhaustive pour Claude Code

**Lis ce fichier en entier avant de créer quoi que ce soit.**
**Après chaque fichier créé, coche la case correspondante dans ## Progression.**
**En cas de doute sur un comportement : relis ce fichier. Ne devine jamais.**

---

## 0. Contexte et philosophie

### Ce qu'est deep-ux
Un plugin Claude Code qui audite n'importe quelle interface numérique de façon exhaustive et autonome. Il tourne sans supervision humaine, peut s'exécuter pendant des heures, et produit des recommandations ancrées sur des faits — jamais sur des suppositions.

### Ce qui distingue deep-ux de tous les outils similaires
1. **Il interview le concepteur avant de rien analyser.** Les recommandations sont contextualisées sur de vrais utilisateurs, pas des personas génériques.
2. **Il sépare strictement 5 disciplines.** Graphisme / UI / UX / Web Design / IHM ont chacun leur agent avec leur vocabulaire propre.
3. **Il ne recommande jamais ce qui n'existe pas dans le code.** Chaque recommandation fonctionnelle est ancrée sur `capabilities.json`.
4. **Il a un vrai œil graphique.** Les agents de graphisme et d'UI sont forcés de décrire précisément avant d'évaluer, avec un vocabulaire technique réel.
5. **Il vérifie la cohérence inter-écrans.** Un agent dédié analyse les contradictions entre tous les écrans après les avoir tous audités.

### Règle anti-drift fondamentale
Chaque agent produit un fichier JSON structuré avec un schéma strict. Ces fichiers sont la mémoire du système. Un agent ne peut jamais "se souvenir" d'une information — il doit la lire dans les fichiers de sa phase précédente.

---

## 1. Structure complète du repo à créer

```
deep-ux/
│
├── README.md                          (déjà existant)
├── SPEC.md                            (ce fichier)
├── CLAUDE.md                          (déjà existant — orchestration master)
├── .gitignore                         (à créer)
│
├── .claude-plugin/
│   └── plugin.json                    (déjà existant)
│
├── commands/
│   └── run.md                         (slash command /deep-ux:run)
│
├── agents/
│   ├── 00-orchestrator.md             (déjà existant — à compléter)
│   ├── 01-interview-conductor.md      (déjà existant — à compléter)
│   ├── 02-capability-mapper.md        (agent)
│   ├── 03-token-extractor-agent.md    (agent)
│   ├── 04-persona-builder.md          (agent)
│   ├── 05-brand-auditor.md            (agent)
│   ├── 06-benchmark-researcher.md     (agent)
│   ├── 07-graphisme-auditor.md        (agent — discipline 1)
│   ├── 08-ui-auditor.md               (agent — discipline 2)
│   ├── 09-ux-auditor.md               (agent — discipline 3)
│   ├── 10-webdesign-auditor.md        (agent — discipline 4)
│   ├── 11-ihm-auditor.md              (agent — discipline 5)
│   ├── 12-screen-dispatcher.md        (agent — lance 07 à 11 pour chaque écran)
│   ├── 13-consistency-checker.md      (agent — cohérence inter-écrans)
│   ├── 14-functional-gap-analyst.md   (agent)
│   └── 15-report-generator.md        (agent)
│
├── scripts/
│   ├── 00-bootstrap.sh                (setup initial)
│   ├── 01-check-deps.sh               (vérification dépendances)
│   ├── 02-discover.py                 (inventaire fichiers + détection stack)
│   ├── 03-build-page-map.py           (cartographie URLs + routes)
│   ├── 04-screenshot.py               (Playwright — captures pleine page)
│   ├── 05-extract-tokens.py           (extraction design tokens CSS)
│   ├── 06-export-session-helper.py    (aide export session SSO)
│   └── lib/
│       ├── auth.py                    (module auth partagé)
│       ├── file_utils.py              (utilitaires fichiers)
│       └── progress.py                (affichage progression terminal)
│
├── skills/
│   └── ux-audit/
│       └── SKILL.md                   (skill globale — vocabulaire + grilles)
│
├── schemas/
│   ├── interview.schema.json          (schéma JSON de validation)
│   ├── capabilities.schema.json
│   ├── design-tokens.schema.json
│   ├── project-map.schema.json
│   ├── personas.schema.json
│   ├── brand.schema.json
│   ├── screen-audit.schema.json       (schéma pour les 5 disciplines)
│   ├── consistency.schema.json
│   ├── functional-gaps.schema.json
│   └── report-cc-tasks.schema.json
│
├── docs/
│   ├── vocabulaire-graphisme.md       (référentiel vocabulaire discipline 1)
│   ├── vocabulaire-ui.md              (référentiel vocabulaire discipline 2)
│   ├── vocabulaire-ux.md              (référentiel vocabulaire discipline 3)
│   ├── vocabulaire-webdesign.md       (référentiel vocabulaire discipline 4)
│   ├── vocabulaire-ihm.md             (référentiel vocabulaire discipline 5)
│   ├── grille-evaluation.md           (critères d'évaluation par discipline)
│   └── anti-drift-rules.md            (règles de contrainte pour chaque agent)
│
└── .audit-template/                   (template du dossier .audit/ à créer)
    ├── .env.example
    └── .gitignore
```

---

## 2. Le .gitignore

```
.audit/
*.pyc
__pycache__/
.DS_Store
node_modules/
```

---

## 3. Les scripts — détail exhaustif

### 00-bootstrap.sh
**Rôle :** Prépare l'environnement de travail. Lancé automatiquement par l'orchestrateur si `.audit/` n'existe pas.
**Ce qu'il fait :**
1. Crée le dossier `.audit/` et tous ses sous-dossiers
2. Copie `.audit-template/.gitignore` dans `.audit/`
3. Copie `.audit-template/.env.example` dans `.audit/.env` si `.audit/.env` n'existe pas
4. Vérifie que `.audit/` est bien dans le `.gitignore` du projet cible — si non, l'y ajoute
5. Affiche un résumé de ce qui a été créé

**Dossiers à créer dans .audit/ :**
```
.audit/
├── .env
├── .gitignore
├── screenshots/
├── screen-audits/
├── phase2/
├── phase4/
└── reports/
```

**Langage :** bash
**Inputs :** aucun
**Outputs :** structure de dossiers `.audit/`
**Anti-drift :** script idempotent — peut être relancé sans écraser ce qui existe

---

### 01-check-deps.sh
**Rôle :** Vérifie que toutes les dépendances sont installées avant de lancer le pipeline.
**Ce qu'il vérifie :**
- Python 3.8+ (`python3 --version`)
- pip (`pip3 --version`)
- playwright (`python3 -c "import playwright"`)
- chromium Playwright (`playwright install chromium --dry-run` ou équivalent)
- Les librairies Python nécessaires : `cssutils`, `beautifulsoup4`, `requests`, `json`

**Comportement si dépendance manquante :**
- Affiche clairement quelle dépendance manque
- Affiche la commande exacte pour l'installer
- S'arrête et retourne exit code 1
- N'essaie JAMAIS d'installer automatiquement sans confirmation

**Langage :** bash
**Outputs :** exit 0 si tout ok, exit 1 avec message clair sinon

---

### 02-discover.py
**Rôle :** Analyse le projet cible et produit une cartographie complète.
**Ce qu'il fait :**
1. Détecte le type de projet (React, Vue, Angular, PHP, HTML statique, autre) en cherchant `package.json`, `composer.json`, `index.php`, etc.
2. Inventorie tous les fichiers par type : `.html`, `.css`, `.scss`, `.js`, `.jsx`, `.tsx`, `.vue`, `.php`, `.py`
3. Détecte le système de routing (React Router, Vue Router, Next.js, etc.)
4. Identifie les fichiers de configuration (`.env.example`, config files)
5. Détecte les dépendances UI majeures (Bootstrap, Tailwind, MUI, Ant Design, etc.)
6. Compte les lignes de code par type de fichier
7. Identifie les points d'entrée (index.html, App.tsx, main.php, etc.)

**Inputs :** chemin du projet cible (argument CLI, défaut = `./`)
**Output :** `.audit/project-map.json` conforme à `schemas/project-map.schema.json`

**Structure de project-map.json :**
```json
{
  "scanned_at": "ISO timestamp",
  "project_root": "/chemin/absolu",
  "stack": {
    "type": "react|vue|angular|php|static|unknown",
    "framework": "next|nuxt|laravel|wordpress|none|unknown",
    "ui_library": "tailwind|bootstrap|mui|antd|none|unknown",
    "router": "react-router|vue-router|next|none|unknown"
  },
  "files": {
    "html": ["liste des chemins"],
    "css": ["liste des chemins"],
    "scss": [],
    "js": [],
    "jsx": [],
    "tsx": [],
    "vue": [],
    "php": [],
    "total_count": 0
  },
  "entry_points": ["liste des fichiers d'entrée"],
  "config_files": ["liste"],
  "dependencies_detected": ["Bootstrap 5.3", "Tailwind 3.x", etc.],
  "loc_by_type": {
    "html": 0,
    "css": 0,
    "js": 0
  }
}
```

**Langage :** Python 3
**Anti-drift :** ne modifie JAMAIS les fichiers du projet cible — lecture seule absolue

---

### 03-build-page-map.py
**Rôle :** Construit la carte exhaustive de toutes les pages/routes accessibles.
**Ce qu'il fait :**
1. Lit `project-map.json` pour connaître le stack
2. **Pour les projets statiques :** liste tous les fichiers `.html`
3. **Pour React/Vue/Angular :** parse les fichiers de routing pour extraire toutes les routes déclarées
4. **Pour PHP/WordPress :** cherche les points d'entrée et les patterns d'URL
5. **Optionnel si URL fournie dans .env :** crawl léger (depth=2, pas de JS) pour trouver les liens internes
6. Produit une liste de pages avec métadonnées

**Output :** `.audit/page-map.json`
```json
{
  "pages": [
    {
      "id": "page-001",
      "url_or_path": "/dashboard",
      "file_source": "src/pages/Dashboard.tsx",
      "requires_auth": true,
      "page_type": "dashboard|form|list|detail|landing|modal|other",
      "screenshot_path": null,
      "audited": false
    }
  ],
  "total_pages": 0,
  "auth_required_count": 0
}
```

**Langage :** Python 3

---

### 04-screenshot.py
**Rôle :** Capture chaque page en pleine hauteur avec Playwright.
**Ce qu'il fait :**
1. Lit `.audit/.env` pour les credentials et l'URL de base
2. Lit `.audit/page-map.json` pour la liste des pages
3. **Si auth requise et type = form :**
   - Navigue vers la page de login
   - Remplit les champs avec les credentials de `.env`
   - Clique Submit
   - Attend la redirection de succès
   - Sauvegarde le storage state dans `.audit/auth-state.json`
4. **Si auth requise et type = sso :**
   - Charge `.audit/auth-state.json` exporté manuellement
5. Pour chaque page : navigue, attend le chargement complet (`networkidle`), capture pleine hauteur
6. Sauvegarde dans `.audit/screenshots/{page-id}.png`
7. Met à jour `page-map.json` avec `screenshot_path` et timestamp

**Variables .env attendues :**
```
BASE_URL=http://localhost:3000
AUTH_TYPE=form|sso|none
AUTH_LOGIN_URL=/login
AUTH_USERNAME=user@example.com
AUTH_PASSWORD=motdepasse
AUTH_SUCCESS_URL=/dashboard
SCREENSHOT_VIEWPORT_WIDTH=1440
SCREENSHOT_VIEWPORT_HEIGHT=900
```

**Comportement en cas d'erreur :**
- Si une page échoue : log l'erreur dans `.audit/screenshot-errors.json`, continue avec la suivante
- Ne s'arrête jamais complètement sur une seule erreur

**Langage :** Python 3 avec Playwright
**Anti-drift :** met à jour `page-map.json` au fur et à mesure, reprend là où il s'est arrêté si relancé

---

### 05-extract-tokens.py
**Rôle :** Extrait tous les design tokens du projet — couleurs, typographie, espacements, ombres, border-radius.
**Ce qu'il fait :**
1. Lit tous les fichiers CSS/SCSS identifiés dans `project-map.json`
2. **Couleurs :** extrait toutes les valeurs hex, rgb, hsl, les variables CSS (`--color-*`), les classes Tailwind utilisées si applicable
3. **Typographie :** familles de polices, tailles utilisées, weights, line-heights, letter-spacing
4. **Espacements :** valeurs de margin, padding, gap — construit l'échelle d'espacement effective
5. **Autres tokens :** border-radius utilisés, box-shadow, z-index scale, breakpoints media queries
6. **Calcule :** ratios de contraste entre les paires couleur/fond les plus fréquentes (WCAG AA = 4.5:1, AAA = 7:1)
7. **Détecte :** si un système de design tokens est présent (variables CSS cohérentes) ou si les valeurs sont "hardcodées" partout

**Output :** `.audit/design-tokens.json`
```json
{
  "colors": {
    "primary": ["#hex", "rgb()", ...],
    "neutral": [],
    "semantic": {"success": "#hex", "error": "#hex", "warning": "#hex"},
    "all_values": [],
    "css_variables": {"--color-primary": "#hex"},
    "has_design_system": true|false
  },
  "typography": {
    "font_families": [{"name": "Inter", "weights": [400, 600], "source": "google|local|system"}],
    "sizes_used": ["12px", "14px", "16px", "24px", "32px"],
    "size_scale": "chaotic|loose|consistent",
    "line_heights_used": ["1.2", "1.5"],
    "dominant_body_size": "16px",
    "dominant_heading_size": "32px"
  },
  "spacing": {
    "values_used": ["4px", "8px", "12px", "16px", "24px", "32px"],
    "scale_type": "4px-grid|8px-grid|chaotic|mixed",
    "base_unit": "8px"
  },
  "borders": {
    "radius_values": ["4px", "8px", "50%"],
    "border_styles": []
  },
  "shadows": [],
  "breakpoints": ["768px", "1024px", "1280px"],
  "contrast_ratios": [
    {"fg": "#333", "bg": "#fff", "ratio": 12.6, "wcag_aa": true, "wcag_aaa": true}
  ],
  "token_coherence_score": 0
}
```

**Langage :** Python 3 avec `cssutils` ou parsing regex si cssutils non dispo
**Anti-drift :** lecture seule sur les fichiers source

---

### 06-export-session-helper.py
**Rôle :** Guide interactif pour exporter une session browser en cas d'auth SSO.
**Ce qu'il fait :**
1. Affiche des instructions claires pour exporter le storage state depuis Chrome/Firefox
2. Lance un petit serveur local temporaire qui attend le fichier exporté
3. Valide le format du fichier reçu
4. Le sauvegarde dans `.audit/auth-state.json`

**Usage :** lancé manuellement par l'utilisateur quand `AUTH_TYPE=sso`
**Langage :** Python 3

---

### lib/auth.py
Module Python partagé entre les scripts. Fonctions :
- `load_env()` : lit `.audit/.env` et retourne un dict
- `get_auth_config()` : retourne la configuration auth
- `load_auth_state()` : charge `.audit/auth-state.json`
- `save_auth_state(state)` : sauvegarde le storage state Playwright

---

### lib/file_utils.py
Module Python partagé. Fonctions :
- `read_json(path)` : lit un JSON, retourne None si absent
- `write_json(path, data)` : écrit un JSON formaté
- `ensure_dir(path)` : crée le dossier si absent
- `slugify(text)` : transforme une URL en nom de fichier valide

---

### lib/progress.py
Module Python partagé. Fonctions :
- `log_phase(n, title, inputs, outputs)` : affiche l'entête de phase
- `log_step(message)` : affiche une étape en cours
- `log_success(message)` : affiche un succès
- `log_error(message)` : affiche une erreur
- `log_skip(message)` : affiche un skip (fichier déjà produit)

---

## 4. Les agents — détail exhaustif

### 00-orchestrator.md (à compléter)
**Comportement détaillé :**

L'orchestrateur commence TOUJOURS par afficher l'état complet du pipeline :
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
deep-ux — État du pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Phase 0 — Interview          [COMPLETE]
✓ Phase 1 — Discovery          [COMPLETE]
→ Phase 2 — Grounding          [EN COURS]
  Phase 3 — Audit écrans       [EN ATTENTE]
  Phase 4 — Cohérence          [EN ATTENTE]
  Phase 5 — Rapports           [EN ATTENTE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Il vérifie l'existence de chaque fichier output attendu pour déterminer l'état de chaque phase.
Il ne spawne JAMAIS deux phases en parallèle — séquentiel strict.
Il peut spawner des agents en parallèle DANS une même phase (ex: Phase 3 — tous les écrans en parallèle).

---

### 01-interview-conductor.md (à compléter)
**Comportement anti-drift :**
- Sauvegarde dans `.audit/interview.json` après CHAQUE réponse
- Si le fichier existe déjà avec `"status": "complete"` → affiche les réponses et demande confirmation avant de recommencer
- Si `"status": "in_progress"` → reprend à la dernière question non répondue

---

### 02-capability-mapper.md (à créer)
**Rôle :** Lit le code source et cartographie toutes les capacités fonctionnelles réelles.
**Inputs :** `project-map.json`
**Output :** `.audit/capabilities.json`

**Ce qu'il cherche dans le code :**
1. **Routes/endpoints** : toutes les routes déclarées (API REST, pages, actions)
2. **Entités de données** : modèles, types TypeScript, schémas de BDD détectés
3. **Actions utilisateur** : boutons, formulaires, interactions déclarées dans le code
4. **Intégrations externes** : APIs tierces appelées, services connectés
5. **Rôles et permissions** : si un système de rôles existe dans le code
6. **Notifications** : si un système de notifications/alertes existe
7. **Export/import** : si des fonctions d'export de données existent
8. **Recherche** : si une fonction de recherche existe
9. **Filtres/tri** : si des fonctions de filtrage existent

**Règle absolue :** il ne DÉDUIT pas des capacités — il les TROUVE dans le code.
Si une capacité est mentionnée dans un commentaire mais pas implémentée → elle est tagguée `"status": "commented_only"`.

**Structure capabilities.json :**
```json
{
  "generated_at": "ISO timestamp",
  "capabilities": [
    {
      "id": "cap-001",
      "name": "Authentification utilisateur",
      "category": "auth|data|navigation|action|integration|notification|export|search|filter|other",
      "description": "Description factuelle de ce que fait cette capacité",
      "evidence": "LoginForm.tsx:45 — fonction handleLogin()",
      "status": "implemented|partial|commented_only",
      "exposed_in_ui": true|false,
      "screens_where_used": ["/login", "/dashboard"]
    }
  ],
  "total_capabilities": 0,
  "implemented_count": 0,
  "partial_count": 0
}
```

---

### 03-token-extractor-agent.md (à créer)
**Rôle :** Agent qui complète et analyse ce que le script `05-extract-tokens.py` a produit.
Il lit `design-tokens.json` et produit une analyse qualitative.
**Note :** Le script fait l'extraction mécanique. Cet agent fait l'interprétation.

**Ce qu'il produit en plus :**
- Évalue la cohérence du système de tokens (score 0-100)
- Identifie les "accidents" typographiques (tailles isolées, familles utilisées une seule fois)
- Classe le système de couleurs (monochrome, analogique, complémentaire, triadique, non-défini)
- Identifie si une grille d'espacement existe réellement

---

### 04-persona-builder.md (à créer)
**Rôle :** Construit des personas riches à partir de l'interview ET de la recherche.
**Inputs :** `interview.json`, `capabilities.json`, `project-map.json`
**Output :** `.audit/phase2/personas.json`

**Ce qu'il fait :**
1. Lit les réponses de l'interview sur les utilisateurs
2. Effectue une recherche web sur le secteur d'activité et le profil utilisateur décrit
3. Croise les informations pour construire 1 à 3 personas (jamais plus de 3)
4. Pour chaque persona :

```json
{
  "id": "persona-001",
  "name": "Prénom fictif représentatif",
  "role": "Titre de poste réel",
  "age_range": "35-45",
  "tech_literacy": "débutant|intermédiaire|expert",
  "context": {
    "work_environment": "bureau fixe|terrain|hybride|mobile",
    "devices": ["desktop", "tablet"],
    "usage_frequency": "quotidien|hebdomadaire|ponctuel",
    "previous_tool": "Excel|logiciel métier|papier|rien"
  },
  "goals": ["Ce qu'il veut accomplir avec le logiciel — liste courte"],
  "frustrations": ["Douleurs connues — issues de l'interview"],
  "mental_model": "Comment ce persona pense que le logiciel devrait fonctionner",
  "cognitive_load_tolerance": "faible|moyen|élevé",
  "key_tasks": ["Les 3 tâches principales dans le logiciel"],
  "success_definition": "Ce que 'bien utiliser le logiciel' signifie pour lui",
  "quote_representative": "Une phrase qui résume son rapport à l'outil"
}
```

**Règle anti-hallucination :** Chaque attribut doit avoir une source explicite :
- `"source": "interview_q4"` si issu d'une réponse d'interview
- `"source": "web_research"` si issu d'une recherche
- `"source": "inferred"` si déduit — avec la déduction expliquée

---

### 05-brand-auditor.md (à créer)
**Rôle :** Audite la cohérence de l'identité de marque dans l'interface.
**Inputs :** `design-tokens.json`, screenshots, `interview.json`
**Output :** `.audit/phase2/brand.json`

**Ce qu'il analyse :**
- Cohérence de la palette couleur avec les valeurs déclarées en interview
- Personnalité typographique (formelle, technique, chaleureuse, neutre, créative)
- Présence ou absence de logo, charte graphique identifiable
- Ton visuel global (minimaliste, dense, corporate, friendly, sérieux)
- Cohérence de ce ton sur tous les écrans

**Vocabulaire forcé :**
L'agent DOIT utiliser ces termes quand applicable :
- Pour les couleurs : teinte, saturation, luminosité, valeur tonale, contraste simultané
- Pour la typographie : empattement, sans-serif, slab, monospace, humaniste, géométrique, transitional
- Pour la personnalité : apollinien/dionysiaque, froid/chaud, statique/dynamique

---

### 06-benchmark-researcher.md (à créer)
**Rôle :** Recherche des interfaces de référence dans le même secteur.
**Inputs :** `interview.json` (secteur, type d'outil), `personas.json`
**Output :** `.audit/phase2/benchmarks.json`

**Ce qu'il fait :**
1. Identifie le secteur et le type d'outil (cockpit IT, CRM, e-commerce back-office, outil métier, etc.)
2. Recherche 3 à 5 interfaces de référence reconnues dans ce secteur
3. Pour chaque référence : note les patterns UX dominants, les conventions visuelles
4. Identifie les "conventions du secteur" que les utilisateurs de ce domaine ont internalisées
5. **Note cruciale :** il ne dit pas "fais comme eux" — il dit "voici ce que tes utilisateurs ont l'habitude de voir, voici ce que tu respectes ou violes"

---

### 07-graphisme-auditor.md (à créer)
**Discipline : GRAPHISME**
**Rôle :** Audite la dimension graphique pure — identité visuelle, composition, couleur comme art.
**Inputs :** screenshot de l'écran, `design-tokens.json`, `brand.json`
**Output :** section `graphisme` dans `screen-{n}.json`

**Ce qu'il DOIT faire avant d'évaluer — la règle de description préalable :**
Avant toute évaluation, l'agent décrit ce qu'il voit avec précision :
```
Je vois : [description factuelle de la composition, couleurs, typographie]
```
Puis il évalue.

**Grille d'évaluation graphisme :**

**1. Composition et mise en page**
- Grille de mise en page : colonnes identifiables ? rapport entre zones ?
- Rapport plein/vide (densité) : correct pour le contexte (outil professionnel vs landing page)
- Axe de lecture dominant (gauche-droite, Z-pattern, F-pattern, E-pattern)
- Hiérarchie visuelle par le poids : est-ce que l'œil sait où aller en premier ?
- Alignements : cohérence des alignements horizontaux et verticaux
- Principe de proximité (Gestalt) : les éléments liés sont-ils regroupés ?

**2. Couleur**
- Nombre de teintes distinctes utilisées (idéal : 2-3 teintes principales + neutres)
- Température dominante (chaude / froide / neutre) et son adéquation au secteur
- Contraste valeurs tonales (pas seulement WCAG — contraste graphique global)
- Cohérence avec `brand.json`
- Accidents chromatiques : couleurs qui "jurent" avec le reste

**3. Typographie comme graphisme**
- Personnalité de la/des police(s) choisie(s) (humaniste, géométrique, mécane, etc.)
- Rapport entre la personnalité typographique et le secteur d'activité
- Contraste de graisse (weight) utilisé comme outil graphique
- Corps de texte : taille, interlignage (leading), approche (tracking)
- Titres : taille, graisse, casse (majuscules, minuscules, mixte)
- Hiérarchie typographique : H1, H2, H3, body, caption — sont-ils vraiment distincts ?

**4. Identité et cohérence**
- Présence d'une identité visuelle identifiable
- Cohérence de style sur cet écran (ne pas mélanger flat design et skeuomorphisme)
- Qualité des iconographies si présentes (style cohérent, taille cohérente)

**Vocabulaire obligatoire :** kerning, leading, tracking, weight, valeur tonale, teinte, saturation, contraste simultané, gestalt, figure/fond, rythme visuel, tension, respiration, focal point.

**Score :** 0-100, justifié par des observations spécifiques.

---

### 08-ui-auditor.md (à créer)
**Discipline : UI (User Interface Design)**
**Rôle :** Audite le système de composants, les états interactifs, la cohérence du design system.
**Inputs :** screenshot, code source de l'écran, `design-tokens.json`
**Output :** section `ui` dans `screen-{n}.json`

**Grille d'évaluation UI :**

**1. Système de composants**
- Les composants similaires sont-ils identiques visuellement ? (cohérence)
- Les boutons primaires/secondaires/tertiaires sont-ils clairement hiérarchisés ?
- Les champs de formulaire sont-ils cohérents entre eux ?
- Les tableaux/listes ont-ils un style uniforme ?

**2. États interactifs**
- Les éléments cliquables sont-ils visuellement identifiables comme tels ? (affordance)
- Les états hover, focus, active, disabled sont-ils définis et cohérents ?
- Les états de chargement (loading) sont-ils gérés visuellement ?
- Les états d'erreur et de succès sont-ils distincts et clairs ?

**3. Système d'espacement**
- La grille d'espacement est-elle cohérente ? (multiple de 4px ou 8px)
- Les paddings internes des composants sont-ils uniformes ?
- Les marges entre sections sont-elles proportionnelles à leur importance ?

**4. Design tokens**
- Les couleurs utilisées correspondent-elles aux tokens définis ?
- Les tailles de texte suivent-elles une échelle ?
- Y a-t-il des valeurs "hardcodées" qui violent le système ?

**5. Densité d'information**
- La densité est-elle adaptée au contexte d'usage (outil professionnel = dense OK, onboarding = aéré) ?
- Y a-t-il des zones sur-chargées qui nécessitent une réorganisation ?

**Vocabulaire obligatoire :** affordance, état (state), design system, token, composant, variant, instance, atomic design, densité, padding, margin, gap, grille, baseline grid.

**Score :** 0-100, justifié.

---

### 09-ux-auditor.md (à créer)
**Discipline : UX (User Experience)**
**Rôle :** Audite l'expérience vécue — parcours, charge cognitive, architecture de l'information.
**Inputs :** screenshot, code source, `personas.json`, `capabilities.json`, `page-map.json`
**Output :** section `ux` dans `screen-{n}.json`

**Grille d'évaluation UX :**

**1. Architecture de l'information**
- L'organisation du contenu correspond-elle au modèle mental du persona ?
- Les catégories/sections sont-elles nommées avec les mots de l'utilisateur (pas du développeur) ?
- La navigation principale reflète-t-elle les tâches les plus fréquentes en premier ?
- Le breadcrumb (fil d'Ariane) est-il présent quand la profondeur le justifie ?

**2. Charge cognitive — Loi de Miller (7±2)**
- Nombre d'éléments dans la navigation principale (idéal : ≤7)
- Nombre d'actions disponibles sur cet écran (trop de choix = paralysie)
- Longueur des formulaires (idéal : max 7 champs visible simultanément)
- Complexité du vocabulaire utilisé (niveau de langue adapté au persona ?)

**3. Parcours et flows**
- La tâche principale du persona sur cet écran est-elle accessible en ≤2 clics ?
- Y a-t-il des impasses (dead ends) ou des sorties de parcours non prévues ?
- Les actions destructives (supprimer, archiver) sont-elles protégées par une confirmation ?
- Le retour en arrière est-il toujours possible ?

**4. Feedback et signalement**
- L'utilisateur sait-il toujours où il en est (indicateurs de progression) ?
- Les actions réussies sont-elles confirmées visuellement ?
- Les erreurs sont-elles expliquées avec des solutions (pas juste "erreur 500") ?

**5. Pertinence pour le persona**
- Cet écran répond-il aux tâches clés de `personas.json` ?
- Des fonctionnalités de `capabilities.json` qui devraient être sur cet écran sont-elles absentes ?

**Vocabulaire obligatoire :** modèle mental, charge cognitive, architecture de l'information, affordance, signifiant, feedback, parcours utilisateur, tâche, sous-tâche, point de friction, dead end, progressive disclosure, onboarding, error recovery.

**Score :** 0-100, justifié.

---

### 10-webdesign-auditor.md (à créer)
**Discipline : WEB DESIGN**
**Rôle :** Audite les spécificités du medium web — responsive, performance perçue, compatibilité.
**Inputs :** screenshot (desktop + mobile si disponible), code source, `design-tokens.json`
**Output :** section `webdesign` dans `screen-{n}.json`

**Grille d'évaluation Web Design :**

**1. Responsive et adaptabilité**
- Les breakpoints définis dans `design-tokens.json` sont-ils réellement utilisés ?
- Le contenu se réorganise-t-il intelligemment sur mobile (pas juste rétréci) ?
- Les touch targets sur mobile font-ils ≥44px (standard iOS/Google) ?
- Les tableaux complexes ont-ils une stratégie mobile (scroll horizontal, vue carte, etc.) ?

**2. Performance perçue**
- Les images sont-elles optimisées (lazy loading détectable dans le code) ?
- Les états de chargement (skeletons, spinners) sont-ils présents ?
- Les animations sont-elles raisonnables (pas de transitions >300ms sur interactions) ?

**3. Typographie web**
- Les polices sont-elles chargées de façon optimale (font-display, subset) ?
- La lisibilité sur écran est-elle respectée (taille corps ≥16px, contraste ≥4.5:1) ?
- Le texte se redimensionne-t-il correctement avec les préférences navigateur ?

**4. Standards web**
- Le HTML est-il sémantique (nav, main, article, section, aside) détectable dans le code ?
- Les liens sont-ils distinguables du texte sans dépendre uniquement de la couleur ?
- Les images ont-elles des attributs alt (WCAG minimal) ?

**Vocabulaire obligatoire :** breakpoint, viewport, touch target, lazy loading, skeleton screen, font-display, above the fold, scroll depth, progressive enhancement, graceful degradation.

**Score :** 0-100, justifié.

---

### 11-ihm-auditor.md (à créer)
**Discipline : IHM (Interface Homme-Machine)**
**Rôle :** Audite la dimension scientifique — ergonomie cognitive, lois de l'interaction, accessibilité.
**Inputs :** screenshot, code source, `personas.json`
**Output :** section `ihm` dans `screen-{n}.json`

**Grille d'évaluation IHM — les lois et principes fondamentaux :**

**1. Loi de Fitts**
- Les cibles cliquables importantes sont-elles suffisamment grandes ?
- Les actions fréquentes sont-elles proches de l'endroit où l'attention se trouve naturellement ?
- Les actions destructives sont-elles éloignées des actions fréquentes ?

**2. Loi de Hick-Hyman**
- Le nombre de choix présentés simultanément est-il raisonnable ?
- Les choix complexes sont-ils divisés en étapes (progressive disclosure) ?
- Y a-t-il des valeurs par défaut intelligentes qui réduisent la décision ?

**3. Loi de Miller (chunks)**
- Les informations sont-elles regroupées en chunks de ≤7 éléments ?
- Les longues listes sont-elles paginées ou filtrables ?

**4. Heuristiques de Nielsen (10)**
Pour cet écran, évaluer chacune :
1. Visibilité de l'état du système
2. Correspondance système/monde réel
3. Contrôle et liberté de l'utilisateur
4. Cohérence et standards
5. Prévention des erreurs
6. Reconnaissance plutôt que rappel
7. Flexibilité et efficacité d'utilisation
8. Design esthétique et minimaliste
9. Aide à la reconnaissance, au diagnostic et à la récupération des erreurs
10. Aide et documentation

**5. Principes de Don Norman**
- Affordances : les possibilités d'action sont-elles perceptibles ?
- Signifiants (signifiers) : les signaux visuels indiquent-ils correctement les affordances ?
- Contraintes : les erreurs impossibles sont-elles impossibles à commettre ?
- Feedback : chaque action déclenche-t-elle un retour perceptible ?
- Modèle conceptuel : l'interface correspond-elle au modèle mental attendu ?

**6. Accessibilité (WCAG 2.1)**
- Niveau A : erreurs bloquantes (images sans alt, formulaires sans label, etc.)
- Niveau AA : objectif standard (contraste 4.5:1, navigation clavier, etc.)
- Niveau AAA : bonnes pratiques (si applicable)

**Vocabulaire obligatoire :** affordance, signifiant, contrainte, feedback, modèle conceptuel, heuristique, charge cognitive, mémoire de travail, chunk, loi de Fitts, loi de Hick, WCAG, ARIA, focus management, skip link.

**Score :** 0-100 par heuristique Nielsen, score global justifié.

---

### 12-screen-dispatcher.md (à créer)
**Rôle :** Lit `page-map.json`, spawne les 5 agents d'audit (07 à 11) pour chaque écran, consolide les résultats.
**Inputs :** `page-map.json`, tous les fichiers Phase 2
**Output :** `.audit/screen-audits/screen-{page-id}.json` pour chaque page

**Structure screen-{n}.json :**
```json
{
  "page_id": "page-001",
  "page_url": "/dashboard",
  "screenshot_path": ".audit/screenshots/page-001.png",
  "audited_at": "ISO timestamp",
  "disciplines": {
    "graphisme": { "score": 72, "observations": [], "recommendations": [] },
    "ui": { "score": 68, "observations": [], "recommendations": [] },
    "ux": { "score": 55, "observations": [], "recommendations": [] },
    "webdesign": { "score": 80, "observations": [], "recommendations": [] },
    "ihm": {
      "score": 61,
      "nielsen_scores": { "h1": 80, "h2": 70, ... "h10": 90 },
      "observations": [],
      "recommendations": []
    }
  },
  "global_score": 67,
  "critical_issues": [],
  "quick_wins": []
}
```

**Règle anti-drift pour les recommendations :**
Chaque recommendation DOIT avoir :
```json
{
  "id": "rec-001",
  "discipline": "ux",
  "priority": "critical|high|medium|low",
  "type": "visual|functional|content|structural",
  "observation": "Ce qui a été observé (factuel)",
  "recommendation": "Ce qui devrait être fait (actionnable)",
  "capability_id": "cap-003 ou null",
  "speculation": false,
  "effort": "xs|s|m|l|xl",
  "wcag_criterion": "1.4.3 ou null"
}
```

---

### 13-consistency-checker.md (à créer)
**Rôle :** Analyse la cohérence ENTRE tous les écrans — Phase 4.
**Inputs :** tous les `screen-{n}.json`, `design-tokens.json`
**Output :** `.audit/phase4/consistency.json`

**Ce qu'il cherche :**
1. **Terminologie incohérente :** un même concept nommé différemment selon les écrans (ex: "Valider" vs "Confirmer" vs "Enregistrer" pour la même action)
2. **Patterns contradictoires :** deux façons différentes de faire la même chose (ex: suppression par bouton sur écran A, par swipe sur écran B)
3. **Incohérences de composants :** même composant qui s'affiche différemment selon le contexte sans raison
4. **Ruptures de navigation :** breadcrumb présent sur certains écrans, absent sur d'autres
5. **Incohérences typographiques :** même niveau de titre avec des tailles différentes
6. **Incohérences de densité :** écrans très différents en densité d'information sans raison de contexte
7. **Faux amis visuels :** deux éléments qui se ressemblent mais font des choses différentes

---

### 14-functional-gap-analyst.md (à créer)
**Rôle :** Croise `capabilities.json` + `personas.json` + résultats d'audit pour identifier ce qui manque.
**Règle absolue :** ne suggère JAMAIS une capacité non présente dans `capabilities.json`
Il peut suggérer de MIEUX EXPOSER une capacité existante.
**Output :** `.audit/phase4/functional-gaps.json`

---

### 15-report-generator.md (à créer)
**Rôle :** Consolide tout en trois formats de rapport.
**Inputs :** tous les fichiers `.audit/`
**Outputs :**
- `report-human.md` : rapport narratif, priorisé, avec opinions claires
- `report-cc-tasks.json` : liste de tickets actionnables pour une session CC d'implémentation
- `report-client.html` : version présentable, avec résumé exécutif

**Structure report-human.md :**
```markdown
# Rapport d'audit deep-ux — [Nom du projet]
## Résumé exécutif (5 lignes max)
## Scores par discipline (tableau)
## Les 3 problèmes critiques
## Analyse par écran
### Écran : [nom]
#### Graphisme
#### UI
#### UX
#### Web Design
#### IHM
## Cohérence inter-écrans
## Gaps fonctionnels
## Recommandations priorisées (MoSCoW)
## Quick wins (impact élevé, effort faible)
```

---

## 5. Les docs/ — référentiels de vocabulaire

Chaque fichier `docs/vocabulaire-{discipline}.md` contient :
- La définition de la discipline (en quoi elle diffère des autres)
- Le vocabulaire technique obligatoire avec définitions courtes
- Les frameworks/méthodes de référence utilisés
- Les pièges à éviter (ce que l'agent NE doit pas dire)

Ces fichiers sont lus par les agents correspondants au démarrage.

---

## 6. La skill globale

### skills/ux-audit/SKILL.md
**Rôle :** Skill auto-activée par CC quand le contexte d'audit UX est détecté.
**Contenu :**
- Les 5 disciplines et leurs périmètres respectifs
- La règle de grounding fonctionnel
- Le vocabulaire transversal
- Le schéma de pensée : décrire → évaluer → recommander (jamais recommander sans avoir décrit)

---

## 7. Règles anti-drift — synthèse

Ces règles s'appliquent à TOUS les agents :

1. **Décrire avant d'évaluer.** Toujours commencer par "Je vois : [description factuelle]" avant toute évaluation.
2. **Citer la source.** Toute observation doit citer le fichier ou screenshot d'où elle vient.
3. **Schema strict.** Tout JSON produit est validé contre son `.schema.json` correspondant.
4. **Pas de dérive fonctionnelle.** Aucune recommendation fonctionnelle sans `capability_id` ou tag `[SPÉCULATION]`.
5. **Pas de généralités.** "La typographie pourrait être améliorée" est interdit. "Le corps de texte en 13px avec un line-height de 1.1 est sous le seuil de lisibilité (recommandé : 16px / 1.5)" est correct.
6. **Reprendre pas recréer.** Si un fichier output existe déjà, l'agent le lit et le complète — ne le recrée pas.
7. **Vocabulaire disciplinaire.** Chaque agent utilise le vocabulaire de sa discipline. Il ne mélange pas les registres.

---

## 8. Ordre de construction par CC

CC doit construire les fichiers dans cet ordre exact :

```
ÉTAPE 1 — Fichiers de base
  .gitignore
  .audit-template/.env.example
  .audit-template/.gitignore

ÉTAPE 2 — Schemas JSON (tous)
  schemas/*.schema.json

ÉTAPE 3 — Docs vocabulaire (tous)
  docs/vocabulaire-*.md
  docs/grille-evaluation.md
  docs/anti-drift-rules.md

ÉTAPE 4 — Scripts lib (modules partagés)
  scripts/lib/auth.py
  scripts/lib/file_utils.py
  scripts/lib/progress.py

ÉTAPE 5 — Scripts principaux
  scripts/00-bootstrap.sh
  scripts/01-check-deps.sh
  scripts/02-discover.py
  scripts/03-build-page-map.py
  scripts/04-screenshot.py
  scripts/05-extract-tokens.py
  scripts/06-export-session-helper.py

ÉTAPE 6 — Skill globale
  skills/ux-audit/SKILL.md

ÉTAPE 7 — Command
  commands/run.md

ÉTAPE 8 — Agents (dans l'ordre numérique)
  agents/00-orchestrator.md    (compléter l'existant)
  agents/01-interview-conductor.md (compléter l'existant)
  agents/02-capability-mapper.md
  agents/03-token-extractor-agent.md
  agents/04-persona-builder.md
  agents/05-brand-auditor.md
  agents/06-benchmark-researcher.md
  agents/07-graphisme-auditor.md
  agents/08-ui-auditor.md
  agents/09-ux-auditor.md
  agents/10-webdesign-auditor.md
  agents/11-ihm-auditor.md
  agents/12-screen-dispatcher.md
  agents/13-consistency-checker.md
  agents/14-functional-gap-analyst.md
  agents/15-report-generator.md

ÉTAPE 9 — Plugin manifest
  .claude-plugin/plugin.json   (mettre à jour avec agents et skills listés)
```

---

## 9. Progression

CC coche chaque item après création :

### Fichiers de base
- [ ] `.gitignore`
- [ ] `.audit-template/.env.example`
- [ ] `.audit-template/.gitignore`

### Schemas
- [ ] `schemas/interview.schema.json`
- [ ] `schemas/capabilities.schema.json`
- [ ] `schemas/design-tokens.schema.json`
- [ ] `schemas/project-map.schema.json`
- [ ] `schemas/personas.schema.json`
- [ ] `schemas/brand.schema.json`
- [ ] `schemas/screen-audit.schema.json`
- [ ] `schemas/consistency.schema.json`
- [ ] `schemas/functional-gaps.schema.json`
- [ ] `schemas/report-cc-tasks.schema.json`

### Docs vocabulaire
- [ ] `docs/vocabulaire-graphisme.md`
- [ ] `docs/vocabulaire-ui.md`
- [ ] `docs/vocabulaire-ux.md`
- [ ] `docs/vocabulaire-webdesign.md`
- [ ] `docs/vocabulaire-ihm.md`
- [ ] `docs/grille-evaluation.md`
- [ ] `docs/anti-drift-rules.md`

### Scripts lib
- [ ] `scripts/lib/auth.py`
- [ ] `scripts/lib/file_utils.py`
- [ ] `scripts/lib/progress.py`

### Scripts principaux
- [ ] `scripts/00-bootstrap.sh`
- [ ] `scripts/01-check-deps.sh`
- [ ] `scripts/02-discover.py`
- [ ] `scripts/03-build-page-map.py`
- [ ] `scripts/04-screenshot.py`
- [ ] `scripts/05-extract-tokens.py`
- [ ] `scripts/06-export-session-helper.py`

### Skill
- [ ] `skills/ux-audit/SKILL.md`

### Command
- [ ] `commands/run.md`

### Agents
- [ ] `agents/00-orchestrator.md`
- [ ] `agents/01-interview-conductor.md`
- [ ] `agents/02-capability-mapper.md`
- [ ] `agents/03-token-extractor-agent.md`
- [ ] `agents/04-persona-builder.md`
- [ ] `agents/05-brand-auditor.md`
- [ ] `agents/06-benchmark-researcher.md`
- [ ] `agents/07-graphisme-auditor.md`
- [ ] `agents/08-ui-auditor.md`
- [ ] `agents/09-ux-auditor.md`
- [ ] `agents/10-webdesign-auditor.md`
- [ ] `agents/11-ihm-auditor.md`
- [ ] `agents/12-screen-dispatcher.md`
- [ ] `agents/13-consistency-checker.md`
- [ ] `agents/14-functional-gap-analyst.md`
- [ ] `agents/15-report-generator.md`

### Plugin manifest
- [ ] `.claude-plugin/plugin.json` (mise à jour finale)

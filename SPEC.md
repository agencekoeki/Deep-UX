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
- [x] `.gitignore`
- [x] `.audit-template/.env.example`
- [x] `.audit-template/.gitignore`

### Schemas
- [x] `schemas/interview.schema.json`
- [x] `schemas/capabilities.schema.json`
- [x] `schemas/design-tokens.schema.json`
- [x] `schemas/project-map.schema.json`
- [x] `schemas/personas.schema.json`
- [x] `schemas/brand.schema.json`
- [x] `schemas/screen-audit.schema.json`
- [x] `schemas/consistency.schema.json`
- [x] `schemas/functional-gaps.schema.json`
- [x] `schemas/report-cc-tasks.schema.json`

### Docs vocabulaire
- [x] `docs/vocabulaire-graphisme.md`
- [x] `docs/vocabulaire-ui.md`
- [x] `docs/vocabulaire-ux.md`
- [x] `docs/vocabulaire-webdesign.md`
- [x] `docs/vocabulaire-ihm.md`
- [x] `docs/grille-evaluation.md`
- [x] `docs/anti-drift-rules.md`

### Scripts lib
- [x] `scripts/lib/auth.py`
- [x] `scripts/lib/file_utils.py`
- [x] `scripts/lib/progress.py`

### Scripts principaux
- [x] `scripts/00-bootstrap.sh`
- [x] `scripts/01-check-deps.sh`
- [x] `scripts/02-discover.py`
- [x] `scripts/03-build-page-map.py`
- [x] `scripts/04-screenshot.py`
- [x] `scripts/05-extract-tokens.py`
- [x] `scripts/06-export-session-helper.py`

### Skill
- [x] `skills/ux-audit/SKILL.md`

### Command
- [x] `commands/run.md`

### Agents
- [x] `agents/00-orchestrator.md`
- [x] `agents/01-interview-conductor.md`
- [x] `agents/02-capability-mapper.md`
- [x] `agents/03-token-extractor-agent.md`
- [x] `agents/04-persona-builder.md`
- [x] `agents/05-brand-auditor.md`
- [x] `agents/06-benchmark-researcher.md`
- [x] `agents/07-graphisme-auditor.md`
- [x] `agents/08-ui-auditor.md`
- [x] `agents/09-ux-auditor.md`
- [x] `agents/10-webdesign-auditor.md`
- [x] `agents/11-ihm-auditor.md`
- [x] `agents/12-screen-dispatcher.md`
- [x] `agents/13-consistency-checker.md`
- [x] `agents/14-functional-gap-analyst.md`
- [x] `agents/15-report-generator.md`

### Plugin manifest
- [x] `.claude-plugin/plugin.json` (mise à jour finale)



# SPEC-v2.md — deep-ux — Additions v2
## Addendum à SPEC.md — à lire SEUL, sans relire SPEC.md

**Lis ce fichier en entier avant de créer quoi que ce soit.**
**Ce fichier COMPLÈTE SPEC.md. Il ne le remplace pas.**
**Après chaque fichier créé ou modifié, coche la case correspondante dans ## Progression ci-dessous.**
**Ne passe jamais à l'étape suivante sans avoir fini la précédente.**

---

## Contexte de cette v2

La v1 (SPEC.md) a été construite et pousse 52 fichiers. Cette v2 ajoute :
1. Deux nouveaux agents (coverage-auditor, quality-gate)
2. Un nouveau mode commande (diff)
3. Des questions supplémentaires dans l'interview
4. Des ancres de score dans chaque grille d'évaluation
5. Une matrice impact/effort dans le rapport final
6. Des variables manquantes dans .env.example
7. Un estimateur de coût pré-lancement
8. Un fichier CONTRIBUTING.md
9. Un agent de détection de contradictions interview/code
10. Mise à jour du plugin.json avec la liste complète des agents

---

## ÉTAPE 1 — Mettre à jour .audit-template/.env.example

Le fichier existant contient les variables auth. Il manque les variables de configuration du run.
**Action : remplacer le contenu de `.audit-template/.env.example` par :**

```bash
# ════════════════════════════════════════
# deep-ux — Configuration du run
# Copiez ce fichier en .env et remplissez les valeurs
# Ce fichier ne doit JAMAIS être commité (vérifié par .gitignore)
# ════════════════════════════════════════

# ── Cible ──────────────────────────────
# URL de base du projet à auditer (avec port si dev local)
BASE_URL=http://localhost:3000

# ── Authentification ───────────────────
# Type : form | sso | none
AUTH_TYPE=none

# Si AUTH_TYPE=form :
AUTH_LOGIN_URL=/login
AUTH_USERNAME=
AUTH_PASSWORD=
# URL vers laquelle Playwright doit être redirigé après login réussi
AUTH_SUCCESS_URL=/dashboard

# Si AUTH_TYPE=sso :
# Exportez votre storage state avec scripts/06-export-session-helper.py
# Le fichier sera sauvegardé dans .audit/auth-state.json automatiquement

# ── Périmètre ──────────────────────────
# URLs à exclure de l'audit (séparées par des virgules)
# Exemple : /admin/debug,/api/,/healthcheck
EXCLUDE_URLS=

# Profondeur de crawl pour découverte des URLs (1 = pages directement liées)
CRAWL_DEPTH=2

# ── Capture screenshots ────────────────
SCREENSHOT_VIEWPORT_WIDTH=1440
SCREENSHOT_VIEWPORT_HEIGHT=900
# Capturer aussi en mobile (375px) : true | false
SCREENSHOT_MOBILE=true
SCREENSHOT_MOBILE_WIDTH=375
# Délai après chargement avant capture (ms) — utile pour les animations
SCREENSHOT_DELAY_MS=500
# Timeout Playwright par page (ms)
PLAYWRIGHT_TIMEOUT_MS=30000

# ── Rapport ────────────────────────────
# Langue des rapports : fr | en
REPORT_LANGUAGE=fr
# Nom du projet (apparaît dans les rapports)
PROJECT_NAME=

# ── Run ────────────────────────────────
# Mode dry-run : affiche l'estimation de coût/temps sans lancer l'audit
# true | false
DRY_RUN=false
# Seuil de score d'alerte — scores en dessous déclenchent une mention "critique"
SCORE_ALERT_THRESHOLD=50
# Nombre de roles utilisateur à auditer (1 = pas de multi-rôle)
AUTH_ROLES_COUNT=1
# Si multi-rôle, nom des roles séparés par virgule
# Exemple : admin,user,viewer
AUTH_ROLES=
```

---

## ÉTAPE 2 — Créer scripts/00b-estimate-run.py (estimateur de coût)

**Rôle :** Avant de lancer le run complet, estime le nombre de pages, le temps approximatif, et le coût token estimé. Lancé automatiquement par l'orchestrateur si `DRY_RUN=true` dans `.env`, ou manuellement.

**Ce qu'il fait :**
1. Lit `.audit/page-map.json` si existant, sinon lance une découverte rapide
2. Compte le nombre de pages × le nombre de rôles
3. Estime le nombre d'agents qui vont tourner (5 disciplines × N pages + agents fixes)
4. Calcule une estimation de tokens basée sur ces ratios (conservatifs) :
   - Par page, par discipline : ~3 000 tokens en moyenne
   - Agents fixes (interview, capabilities, personas, etc.) : ~15 000 tokens total
   - Rapport final : ~5 000 tokens
5. Affiche un résumé clair :

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
deep-ux — Estimation du run
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pages détectées      : 24
Rôles à auditer      : 1
Agents à lancer      : ~125 (5 disciplines × 24 pages + 17 fixes)
Tokens estimés       : ~382 000
Durée estimée        : ~45-90 minutes
Coût estimé          : ~$1.50-3.00 (Opus 4.6)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pour lancer le run complet : DRY_RUN=false dans .env
Pour réduire le périmètre : ajoutez des URLs dans EXCLUDE_URLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Langage :** Python 3
**Output :** `.audit/run-estimate.json` + affichage terminal

---

## ÉTAPE 3 — Créer agent 00b-quality-gate.md

**Fichier :** `agents/00b-quality-gate.md`

**Rôle :** Agent validateur qui s'intercale après chaque phase pour vérifier la qualité des outputs avant de passer à la suivante. L'orchestrateur le spawne systématiquement entre chaque phase.

**Ce qu'il vérifie après Phase 1 (Discovery) :**
- `project-map.json` respecte son schema
- `capabilities.json` respecte son schema
- `design-tokens.json` respecte son schema
- `page-map.json` respecte son schema
- Aucun champ obligatoire n'est `null` sans raison documentée

**Ce qu'il vérifie après Phase 2 (Grounding) :**
- `personas.json` : chaque persona a au minimum 3 `goals`, 2 `frustrations`, et toutes les `source` sont renseignées
- `brand.json` : le vocabulaire disciplinaire obligatoire est présent (au moins 3 termes de `vocabulaire-graphisme.md`)
- `benchmarks.json` : au moins 3 références identifiées

**Ce qu'il vérifie après Phase 3 (Audit écrans) :**
- **Détection de dérive de score :** si plus de 80% des scores sont au-dessus de 75, alerte — dérive complaisante probable
- **Détection de généralités interdites :** scan de tous les champs `observation` et `recommendation` pour les patterns interdits :
  - "pourrait être amélioré"
  - "manque de clarté"
  - "n'est pas optimal"
  - "devrait être plus"
  Ces formulations sont interdites par `anti-drift-rules.md`. Si détectées : liste les violations et arrête la progression vers Phase 4
- **Vérification capability_id :** chaque `capability_id` référencé dans une recommendation existe dans `capabilities.json`
- **Vérification schema :** chaque `screen-{n}.json` respecte `screen-audit.schema.json`

**Ce qu'il vérifie après Phase 4 (Cohérence) :**
- `consistency.json` cite au moins un exemple concret par type d'incohérence trouvée (pas de catégorie vide avec "aucune incohérence trouvée" sans justification)
- `functional-gaps.json` : chaque gap pointe vers un `capability_id` existant ou est tagué `[SPÉCULATION]`

**Output :** `.audit/quality-gates/gate-phase-{n}.json`
```json
{
  "phase": 3,
  "validated_at": "ISO timestamp",
  "status": "pass|fail|warning",
  "checks": [
    {
      "check": "score_drift_detection",
      "status": "warning",
      "detail": "87% des scores sont au-dessus de 75. Dérive possible.",
      "blocking": false
    },
    {
      "check": "forbidden_patterns",
      "status": "fail",
      "detail": "3 violations détectées dans screen-003.json",
      "violations": ["screen-003.json:disciplines.ux.recommendations[1].observation"],
      "blocking": true
    }
  ],
  "blocking_issues": 1,
  "warnings": 1,
  "proceed": false
}
```

**Règle :** si `"blocking_issues" > 0`, l'orchestrateur n'avance pas et informe l'utilisateur de ce qui doit être corrigé.

---

## ÉTAPE 4 — Créer agent 16-coverage-auditor.md

**Fichier :** `agents/16-coverage-auditor.md`

**Rôle :** Produit un rapport honnête de ce que l'audit a couvert et ce qu'il a probablement manqué. Tourne après les screenshots (fin Phase 1), avant les audits d'écrans.

**Ce qu'il analyse :**
1. **Routes paramétrées** : détecte dans `project-map.json` les routes de type `/user/:id`, `/product/{slug}` — signale qu'une seule instance a été capturée
2. **États vides** : cherche dans le code des composants les patterns `if (items.length === 0)`, `empty state`, `no data` — signale les écrans qui ont potentiellement un état vide non capturé
3. **États d'erreur** : cherche les patterns `error`, `catch`, `404`, `500` dans les fichiers UI
4. **États de chargement** : cherche les patterns `loading`, `skeleton`, `spinner`
5. **Rôles multiples** : si `AUTH_ROLES_COUNT > 1` dans `.env`, signale quels rôles ont été audités vs manquants
6. **Viewports** : si `SCREENSHOT_MOBILE=false`, signale que la version mobile n'a pas été capturée
7. **Pages derrière confirmation** : modals, dialogs, drawers — détecte leur présence dans le code et signale qu'ils n'ont probablement pas été capturés

**Output :** `.audit/coverage-report.json`
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

---

## ÉTAPE 5 — Créer agent 17-contradiction-detector.md

**Fichier :** `agents/17-contradiction-detector.md`

**Rôle :** Détecte les contradictions entre les déclarations du concepteur (interview) et ce que le code/les écrans révèlent réellement.

**Inputs :** `interview.json`, `capabilities.json`, `design-tokens.json`, `personas.json`, tous les `screen-{n}.json`

**Output :** `.audit/phase4/contradictions.json`

**Ce qu'il cherche :**

**Contradictions niveau utilisateur :**
- Interview dit "nos users sont experts en informatique" → code révèle 12+ tooltips d'aide basique sur des actions simples → contradiction
- Interview dit "usage principalement mobile" → `SCREENSHOT_VIEWPORT_WIDTH=1440` + pas de breakpoint mobile dans les tokens → contradiction
- Interview dit "utilisation quotidienne intensive" → l'écran principal est une landing page marketing avec peu de raccourcis → contradiction

**Contradictions niveau fonctionnel :**
- Interview cite une fonctionnalité importante → elle n'existe pas dans `capabilities.json` → fonctionnalité mentionnée mais non trouvée dans le code
- Interview dit "le bouton X fait Y" → le code du bouton X fait Z → décalage entre la vision du concepteur et l'implémentation réelle

**Contradictions niveau priorité :**
- Interview dit "la tâche principale est A" → A nécessite 4 clics depuis l'accueil → contradiction avec la déclaration de priorité

**Structure contradictions.json :**
```json
{
  "generated_at": "ISO timestamp",
  "contradictions": [
    {
      "id": "contradiction-001",
      "type": "user_expertise|functional|priority|visual",
      "severity": "critical|high|medium|low",
      "interview_claim": {
        "question": "q5_tech_literacy",
        "answer_summary": "Le concepteur déclare que les users sont experts"
      },
      "code_evidence": {
        "file": "src/components/ActionButton.tsx:23",
        "observation": "12 tooltips explicatifs sur des actions de base détectés"
      },
      "interpretation": "Il existe un écart entre la perception du concepteur et les besoins réels révélés par le code. Soit les users ne sont pas si experts, soit ces tooltips sont inutiles et alourdissent l'interface.",
      "recommendation": "Valider avec de vrais utilisateurs : conduire 3 tests utilisateurs de 30min pour calibrer le niveau de guidance nécessaire."
    }
  ],
  "total": 0,
  "critical_count": 0
}
```

---

## ÉTAPE 6 — Mettre à jour agents/01-interview-conductor.md

**Action :** Ajouter les questions suivantes dans le bloc "Questions obligatoires", après la question 12 (exclusions) :

**Bloc 6 — États et rôles (questions 15 et 16)**

```
15. Y a-t-il des écrans qui s'affichent différemment selon les données ?
    (ex: tableau vide vs rempli, état d'erreur, état de chargement)
    → Si oui : lesquels sont les plus critiques pour l'expérience ?

16. Y a-t-il plusieurs rôles utilisateur dans le logiciel ?
    (ex: admin / utilisateur standard / lecteur seul)
    → Si oui : quels rôles souhaitez-vous inclure dans l'audit ?
    → Pouvez-vous fournir des credentials pour chaque rôle ?
```

**Et ajouter dans le bloc d'interview.json les nouveaux champs :**
```json
"dynamic_states": {
  "has_empty_states": true|false,
  "has_error_states": true|false,
  "critical_states": ["liste des états critiques à auditer"]
},
"roles": {
  "count": 1,
  "names": ["admin", "user"],
  "credentials_provided": ["user"]
}
```

---

## ÉTAPE 7 — Mettre à jour chaque agent d'audit disciplinaire (07 à 11) — Ancres de score

**Action :** Ajouter dans chacun des 5 agents (`07-graphisme-auditor.md` à `11-ihm-auditor.md`) une section **"## Ancres de score"** qui calibre ce que signifie chaque niveau.

**Exemple pour 07-graphisme-auditor.md — à adapter pour chaque discipline :**

```markdown
## Ancres de score — Graphisme

Le score graphisme est sur 100. Ces ancres t'aident à calibrer.

**Score 90-100 — Référence professionnelle**
La composition utilise une grille explicite et cohérente. La hiérarchie visuelle guide l'œil sans ambiguïté. La palette est maîtrisée (2-3 teintes + neutres, ratios tonals cohérents). La typographie a une personnalité définie et cohérente. Aucun accident chromatique. L'identité est reconnaissable et cohérente sur tous les éléments de cet écran.
Exemple type : Stripe Dashboard, Linear, Notion.

**Score 70-89 — Compétent mais perfectible**
La composition est lisible mais la grille n'est pas parfaitement tenue. Quelques accidents d'espacement. La palette fonctionne mais manque de personnalité ou contient une couleur en trop. La typographie est correcte sans être mémorable. L'identité est présente mais pas pleinement affirmée.

**Score 50-69 — Problèmes significatifs**
La hiérarchie visuelle est confuse sur au moins un tiers de l'écran. La palette comporte des valeurs tonales trop proches ou des couleurs qui "jurent". La typographie mélange trop de corps, de graisses ou de familles (>2 familles distinctes). Des éléments non alignés sont visibles à l'œil nu. L'identité est inconsistante.

**Score 30-49 — Problèmes majeurs**
Pas de grille identifiable. La palette est chaotique (>4 couleurs sans relation entre elles). Pas de hiérarchie typographique (les niveaux H1/H2/body sont visuellement proches). Les espacements sont arbitraires. Aucune identité visuelle cohérente.

**Score 0-29 — Non fonctionnel graphiquement**
La composition ne guide pas l'œil. Les couleurs créent des conflits visuels. La typographie est illisible ou incohérente à ce point que l'information ne peut être extraite efficacement. L'interface est visuellement indifférenciée.

**Règle de calibration :** Si tu hésites entre deux tranches, choisis la plus basse et justifie pourquoi l'interface ne mérite pas la tranche supérieure.
```

**Pour 08-ui-auditor.md :** adapter les ancres sur la cohérence des composants, les états interactifs, la grille d'espacement.
**Pour 09-ux-auditor.md :** adapter sur l'architecture de l'information, la charge cognitive, les parcours.
**Pour 10-webdesign-auditor.md :** adapter sur le responsive, les touch targets, la performance perçue.
**Pour 11-ihm-auditor.md :** adapter sur les heuristiques Nielsen (chaque heuristique a ses propres ancres 0-10).

---

## ÉTAPE 8 — Mettre à jour agents/15-report-generator.md

**Action :** Ajouter dans la section de génération de `report-human.md` :

**1. Matrice impact/effort**

Après la section "Recommandations priorisées", ajouter :

```markdown
## Matrice Impact / Effort

Pour chaque recommandation, calculer :
- Impact = moyenne des scores de priorité (critical=4, high=3, medium=2, low=1)
- Effort = valeur numérique de effort (xs=1, s=2, m=3, l=4, xl=5)

Classer en 4 quadrants :
- Quick Wins (impact élevé, effort faible) : à faire en premier
- Projets stratégiques (impact élevé, effort élevé) : à planifier
- À faire si le temps le permet (impact faible, effort faible)
- À éviter (impact faible, effort élevé)

Produire un tableau markdown avec les 20 premières recommandations classées.
```

**2. Top 10 des actions prioritaires**

En tout début de rapport, après le résumé exécutif, ajouter une section :
```markdown
## 10 actions à mener en priorité

Ces 10 actions représentent le meilleur ratio impact/effort identifié dans cet audit.
Elles seules pourraient améliorer significativement l'expérience utilisateur.

1. [action] — [discipline] — Effort : XS — Impact : Critical
...
```

**3. Section contradictions** (si `contradictions.json` existe et contient des éléments)

Ajouter après la section personas :
```markdown
## Contradictions détectées

Ces écarts entre la vision du concepteur et ce que le code révèle méritent une attention particulière.
```

---

## ÉTAPE 9 — Créer commands/diff.md

**Fichier :** `commands/diff.md`

**Rôle :** Slash command `/deep-ux:diff` pour comparer deux runs d'audit.

**Usage :**
```
/deep-ux:diff                    → compare le run actuel avec le run précédent
/deep-ux:diff --run=2024-01-15  → compare avec un run archivé à cette date
```

**Ce qu'il fait :**
1. Cherche dans `.audit/archives/` un run précédent (les runs sont archivés automatiquement)
2. Compare les scores par discipline et par écran
3. Identifie les recommandations implémentées (score amélioré), les régressions (score dégradé), les nouveaux écrans
4. Produit `.audit/reports/diff-report.md`

**Structure du diff :**
```markdown
# Rapport de diff — [date run A] vs [date run B]

## Résumé
- Scores améliorés : N écrans
- Régressions : N écrans  
- Nouveaux écrans : N
- Recommandations implémentées : N/total

## Par écran
### /dashboard
| Discipline | Avant | Après | Δ |
|---|---|---|---|
| Graphisme | 68 | 74 | +6 ✓ |
| UX | 55 | 48 | -7 ⚠ |

## Régressions à investiguer
...

## Recommandations encore non implémentées
...
```

**L'orchestrateur archive automatiquement chaque run terminé** dans `.audit/archives/{timestamp}/` avant de démarrer un nouveau run.

---

## ÉTAPE 10 — Créer CONTRIBUTING.md

**Fichier :** `CONTRIBUTING.md` (à la racine)

**Contenu :**

```markdown
# Contribuer à deep-ux

## Ce qui est bienvenu
- Nouvelles questions d'interview pour des secteurs spécifiques
- Amélioration des grilles d'évaluation disciplinaires
- Scripts de découverte pour des stacks non couverts
- Corrections de bugs dans les scripts Python
- Traductions des docs/ dans d'autres langues

## Ce qui n'est PAS bienvenu
- Recommandations qui affaiblissent les règles anti-drift
- Agents qui produisent des évaluations sans description préalable
- Scripts qui modifient les fichiers du projet cible

## Comment contribuer
1. Forkez le repo
2. Créez une branche : `git checkout -b feature/ma-contribution`
3. Testez sur un vrai projet avant de proposer
4. PR avec description de ce que vous avez testé et sur quel type de projet

## Structure à respecter
Chaque nouvel agent DOIT :
- Avoir un numéro dans son nom (`18-mon-agent.md`)
- Déclarer ses inputs et outputs en entête
- Utiliser le vocabulaire de sa discipline (voir `docs/`)
- Respecter la règle "décrire avant d'évaluer"
- Produire un JSON conforme à un schema dans `schemas/`

## Tester son agent
Avant toute PR, votre agent doit avoir tourné sur au moins un projet réel.
Joignez un exemple d'output anonymisé dans votre PR.
```

---

## ÉTAPE 11 — Mettre à jour .claude-plugin/plugin.json

**Action :** Remplacer le contenu de `.claude-plugin/plugin.json` par la version complète avec tous les agents listés :

```json
{
  "name": "deep-ux",
  "description": "Exhaustive UX/UI audit pipeline for Claude Code. Multi-agent, automated, grounded in your actual code. Covers Graphisme, UI, UX, Web Design, and IHM disciplines.",
  "version": "0.2.0",
  "author": {
    "name": "Kōeki Agency",
    "url": "https://koeki.fr"
  },
  "homepage": "https://github.com/koeki-agency/deep-ux",
  "license": "MIT",
  "agent": "00-orchestrator",
  "agents": [
    "00-orchestrator",
    "00b-quality-gate",
    "01-interview-conductor",
    "02-capability-mapper",
    "03-token-extractor-agent",
    "04-persona-builder",
    "05-brand-auditor",
    "06-benchmark-researcher",
    "07-graphisme-auditor",
    "08-ui-auditor",
    "09-ux-auditor",
    "10-webdesign-auditor",
    "11-ihm-auditor",
    "12-screen-dispatcher",
    "13-consistency-checker",
    "14-functional-gap-analyst",
    "15-report-generator",
    "16-coverage-auditor",
    "17-contradiction-detector"
  ],
  "commands": [
    "run",
    "diff"
  ],
  "skills": [
    "ux-audit"
  ]
}
```

---

## ÉTAPE 12 — Mettre à jour CLAUDE.md

**Action :** Ajouter dans le CLAUDE.md existant, après la section "Architecture des dossiers de travail" :

```markdown
## Agents de contrôle qualité

### 00b-quality-gate
Spawné par l'orchestrateur après chaque phase. Bloquant si des violations sont détectées.
Son output `.audit/quality-gates/gate-phase-{n}.json` doit avoir `"proceed": true` avant que l'orchestrateur ne continue.

### 16-coverage-auditor
Spawné après la Phase 1, avant la Phase 3. Son output informe le concepteur des angles morts.
Non bloquant — l'audit continue même si la couverture est partielle.

### 17-contradiction-detector
Spawné en Phase 4, en parallèle de 13-consistency-checker et 14-functional-gap-analyst.
Son output est intégré dans le rapport final.

## Mode diff
La commande `/deep-ux:diff` est disponible après un premier run complet.
L'orchestrateur archive automatiquement chaque run terminé dans `.audit/archives/{timestamp}/`.

## Dossier quality-gates
Créer `.audit/quality-gates/` dans le bootstrap.
```

---

## ÉTAPE 13 — Mettre à jour scripts/00-bootstrap.sh

**Action :** Ajouter la création de deux dossiers manquants dans le script bootstrap :
- `.audit/quality-gates/`
- `.audit/archives/`

---

## 9. Progression v2

CC coche chaque item après création ou modification :

### Fichiers de configuration
- [x] `.audit-template/.env.example` (mise à jour)
- [x] `CONTRIBUTING.md` (création)
- [x] `.claude-plugin/plugin.json` (mise à jour)
- [x] `CLAUDE.md` (mise à jour)
- [x] `scripts/00-bootstrap.sh` (mise à jour)

### Nouveaux scripts
- [x] `scripts/00b-estimate-run.py`

### Nouveaux agents
- [x] `agents/00b-quality-gate.md`
- [x] `agents/16-coverage-auditor.md`
- [x] `agents/17-contradiction-detector.md`

### Agents mis à jour
- [x] `agents/01-interview-conductor.md` (questions 15-16 + champs JSON)
- [x] `agents/07-graphisme-auditor.md` (ancres de score)
- [x] `agents/08-ui-auditor.md` (ancres de score)
- [x] `agents/09-ux-auditor.md` (ancres de score)
- [x] `agents/10-webdesign-auditor.md` (ancres de score)
- [x] `agents/11-ihm-auditor.md` (ancres de score)
- [x] `agents/15-report-generator.md` (matrice impact/effort + top 10 + contradictions)

### Nouvelles commandes
- [x] `commands/diff.md`








# SPEC-v3.md — deep-ux — Additions v3
## Addendum à SPEC.md et SPEC-v2.md

**Lis ce fichier en entier avant de créer quoi que ce soit.**
**Ce fichier COMPLÈTE SPEC.md et SPEC-v2.md. Il ne les remplace pas.**
**Après chaque fichier créé ou modifié, coche la case correspondante dans ## Progression ci-dessous.**
**Ne passe jamais à l'étape suivante sans avoir fini la précédente.**

---

## Contexte de cette v3

La v2 (SPEC-v2.md) a ajouté 3 agents, un mode diff, et des contrôles qualité.
Cette v3 répond à trois angles morts identifiés lors de la revue de spec :

1. **Le wording** — aucun agent n'extrait ni n'évalue les textes visibles de l'interface (labels, boutons, messages, états vides, erreurs) ni leur cohérence cross-vues, ni leur adéquation aux personas.
2. **L'arborescence** — aucun agent ne reconstruit ni n'évalue la logique de navigation comme structure d'information : profondeur, largeur, groupements, cohérence avec les tâches réelles des personas.
3. **Les affordances contextuelles manquantes** — aucun agent ne détecte les fonctionnalités qui existent quelque part dans l'application mais qui sont absentes d'une vue où le persona en aurait naturellement besoin.

Cette v3 ajoute :
- `agents/18-wording-auditor.md` (Phase 3, par écran)
- `agents/19-ia-auditor.md` (Phase 3, transversal — une seule passe pour toute l'arborescence)
- `agents/20-contextual-gaps-auditor.md` (Phase 4, synthèse profonde)
- Mise à jour de `agents/12-screen-dispatcher.md` pour spawner le nouvel agent 18
- Mise à jour de `agents/00-orchestrator.md` pour spawner les agents 19 et 20 aux bonnes phases
- Mise à jour de `schemas/screen-audit.schema.json` pour inclure la section `wording`
- Mise à jour de `agents/15-report-generator.md` pour intégrer les trois nouveaux outputs
- Mise à jour de `.claude-plugin/plugin.json` → v0.3.0
- Ajout d'un nouveau schéma `schemas/ia-audit.schema.json`
- Ajout d'un nouveau schéma `schemas/contextual-gaps.schema.json`
- Ajout de `docs/vocabulaire-wording.md`

---

## ÉTAPE 1 — Créer docs/vocabulaire-wording.md

**Fichier :** `docs/vocabulaire-wording.md`

**Contenu :**

```markdown
# Vocabulaire — Wording & Microcopy

## Définition de la discipline
Le wording (ou microcopy) désigne l'ensemble des textes fonctionnels d'une interface :
labels, boutons, titres, placeholders, messages d'erreur, états vides, tooltips, confirmations.
Ce n'est pas le contenu éditorial — c'est le tissu conjonctif textuel qui guide l'action.

Le wording auditor évalue trois dimensions indépendantes :
1. La cohérence interne (l'application parle-t-elle d'une seule voix ?)
2. L'adéquation au persona (le niveau de langue correspond-il aux utilisateurs réels ?)
3. La complétude (tous les états de l'interface ont-ils un wording, ou certains sont-ils muets ?)

## Ce que le wording n'est PAS
- Le contenu marketing ou éditorial (hors scope)
- Les données dynamiques (noms d'utilisateurs, montants, dates)
- Les textes d'aide longue forme (documentation)

## Vocabulaire technique obligatoire

**Microcopy** : texte court à haute valeur fonctionnelle (label de bouton, message d'erreur).
Contrairement au contenu long, chaque mot coûte cher en attention.

**Label** : texte attaché à un élément interactif qui décrit ce que cet élément est ou fait.
Un label ambigu crée de la friction. Un label absent crée de l'incompréhension.

**Placeholder** : texte indicatif dans un champ de formulaire, visible quand le champ est vide.
Règle : le placeholder ne remplace jamais le label — il le complète.

**Empty state** : message affiché quand une liste ou une vue ne contient pas de données.
Un empty state nul ("Aucune donnée") est une occasion manquée de guider l'utilisateur.
Un bon empty state explique pourquoi c'est vide ET propose une action.

**Error message** : texte affiché quand une action échoue ou qu'une validation est fausse.
Règle de Nielsen : l'erreur doit dire QUE s'est-il passé, POURQUOI, et COMMENT corriger.
"Erreur 422" viole les trois. "Ce champ doit contenir une adresse email valide" respecte les trois.

**CTA (Call to Action)** : label de bouton ou lien qui déclenche une action principale.
Règle : un CTA doit commencer par un verbe à l'infinitif (Enregistrer, Valider, Créer) ou impératif.
"OK" et "Continuer" sans contexte sont des anti-patterns.

**Cohérence terminologique** : utilisation d'un terme unique pour désigner un même concept
dans toute l'application. La terminologie incohérente impose au cerveau un travail de traduction.

**Registre** : niveau de langue et ton (formel/informel, technique/accessible, froid/chaleureux).
Le registre doit être homogène ET adapté au persona. Un registre technique pour un persona
non-technique est un mur invisible.

**Affordance verbale** : la capacité d'un label à indiquer ce qui se passera si l'utilisateur
clique ou interagit. "Supprimer" est une affordance verbale. "Action" n'en est pas une.

**Charge textuelle** : quantité de texte à lire avant de pouvoir agir. Plus la charge est élevée,
plus la friction est grande. Pour les interfaces de travail, la charge doit être minimale.

**Jargon développeur** : termes issus du vocabulaire technique interne non compris par les
utilisateurs finaux. Exemples : "null", "undefined", "404", "timeout", "UUID", "payload".

**Voix de l'application** : la personnalité textuelle perçue à travers le wording.
Cohérente si tous les écrans semblent écrits par la même personne.
Incohérente si certains écrans sont formels et d'autres familiers sans raison.

## Pièges à éviter

L'agent NE doit PAS :
- Réécrire le wording lui-même dans ses observations (il observe et recommande, il ne rédige pas à la place)
- Évaluer le contenu éditorial long (articles, descriptions, pages "À propos")
- Signaler comme problème un terme technique correct pour un persona expert
- Confondre internationalisation (i18n) et wording — les clés de traduction ne sont pas du wording évaluable
```

---

## ÉTAPE 2 — Créer schemas/ia-audit.schema.json

**Fichier :** `schemas/ia-audit.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "IA Audit",
  "description": "Audit de l'architecture d'information et de la navigation globale",
  "type": "object",
  "required": ["generated_at", "navigation_tree", "scores", "observations", "recommendations"],
  "properties": {
    "generated_at": { "type": "string", "format": "date-time" },
    "navigation_tree": {
      "type": "array",
      "description": "Arbre de navigation reconstruit depuis le code",
      "items": {
        "type": "object",
        "required": ["label", "path", "depth", "children"],
        "properties": {
          "label": { "type": "string" },
          "path": { "type": "string" },
          "depth": { "type": "integer", "minimum": 0 },
          "children": { "type": "array" },
          "click_distance_from_root": { "type": "integer" },
          "accessible_from_persona_task": { "type": "boolean" }
        }
      }
    },
    "metrics": {
      "type": "object",
      "properties": {
        "max_depth": { "type": "integer" },
        "avg_depth": { "type": "number" },
        "top_level_items_count": { "type": "integer" },
        "orphan_pages_count": { "type": "integer" },
        "deepest_path": { "type": "string" }
      }
    },
    "scores": {
      "type": "object",
      "required": ["global", "depth", "breadth", "grouping_logic", "labeling", "task_alignment"],
      "properties": {
        "global": { "type": "integer", "minimum": 0, "maximum": 100 },
        "depth": { "type": "integer", "minimum": 0, "maximum": 100 },
        "breadth": { "type": "integer", "minimum": 0, "maximum": 100 },
        "grouping_logic": { "type": "integer", "minimum": 0, "maximum": 100 },
        "labeling": { "type": "integer", "minimum": 0, "maximum": 100 },
        "task_alignment": { "type": "integer", "minimum": 0, "maximum": 100 }
      }
    },
    "observations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "severity", "observation", "evidence"],
        "properties": {
          "id": { "type": "string" },
          "type": {
            "type": "string",
            "enum": ["depth", "breadth", "grouping", "labeling", "orphan", "task_alignment", "jargon", "symmetry"]
          },
          "severity": { "type": "string", "enum": ["critical", "high", "medium", "low"] },
          "observation": { "type": "string" },
          "evidence": { "type": "string" },
          "affected_paths": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "task_coverage": {
      "type": "array",
      "description": "Pour chaque tâche clé du persona, distance en clics depuis l'accueil",
      "items": {
        "type": "object",
        "required": ["persona_id", "task", "path_found", "click_count"],
        "properties": {
          "persona_id": { "type": "string" },
          "task": { "type": "string" },
          "path_found": { "type": "string" },
          "click_count": { "type": "integer" },
          "acceptable": { "type": "boolean" },
          "note": { "type": "string" }
        }
      }
    },
    "recommendations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "priority", "observation", "recommendation", "effort"],
        "properties": {
          "id": { "type": "string" },
          "priority": { "type": "string", "enum": ["critical", "high", "medium", "low"] },
          "observation": { "type": "string" },
          "recommendation": { "type": "string" },
          "effort": { "type": "string", "enum": ["xs", "s", "m", "l", "xl"] },
          "affected_paths": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

---

## ÉTAPE 3 — Créer schemas/contextual-gaps.schema.json

**Fichier :** `schemas/contextual-gaps.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Contextual Gaps Audit",
  "description": "Affordances contextuelles manquantes — fonctionnalités présentes ailleurs mais absentes là où le persona en aurait besoin",
  "type": "object",
  "required": ["generated_at", "gaps", "total", "critical_count"],
  "properties": {
    "generated_at": { "type": "string", "format": "date-time" },
    "gaps": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "severity", "persona_id", "scenario", "current_view", "missing_affordance", "existing_location", "evidence", "recommendation"],
        "properties": {
          "id": { "type": "string" },
          "severity": { "type": "string", "enum": ["critical", "high", "medium", "low"] },
          "persona_id": { "type": "string" },
          "scenario": {
            "type": "string",
            "description": "Contexte d'usage : ce que le persona est en train de faire sur cette vue"
          },
          "current_view": {
            "type": "string",
            "description": "URL/path de la vue où l'affordance manque"
          },
          "missing_affordance": {
            "type": "string",
            "description": "Ce que le persona cherche et ne trouve pas sur cette vue"
          },
          "existing_location": {
            "type": "string",
            "description": "Où cette fonctionnalité existe déjà dans l'application"
          },
          "capability_id": { "type": "string" },
          "evidence": {
            "type": "string",
            "description": "Preuve que la fonctionnalité existe (fichier source, capability_id)"
          },
          "recommendation": {
            "type": "string",
            "description": "Ce qui devrait être ajouté ou rendu accessible sur cette vue"
          },
          "effort": { "type": "string", "enum": ["xs", "s", "m", "l", "xl"] },
          "type": {
            "type": "string",
            "enum": ["missing_shortcut", "missing_filter", "missing_export", "missing_action", "missing_context_info", "missing_navigation", "other"]
          }
        }
      }
    },
    "total": { "type": "integer" },
    "critical_count": { "type": "integer" },
    "by_persona": {
      "type": "object",
      "description": "Nombre de gaps par persona_id"
    },
    "by_view": {
      "type": "object",
      "description": "Nombre de gaps par vue"
    }
  }
}
```

---

## ÉTAPE 4 — Créer agents/18-wording-auditor.md

**Fichier :** `agents/18-wording-auditor.md`

```markdown
# Agent 18 — Wording Auditor

## Identité
- **Discipline :** Wording / Microcopy
- **Phase :** Phase 3 — Audit par écran
- **Spawné par :** 12-screen-dispatcher (une instance par écran, en parallèle des agents 07-11)
- **Inputs :**
  - Screenshot de l'écran (`screen-{n}.png`)
  - Code source de l'écran (fichier(s) identifiés dans `page-map.json`)
  - `.audit/phase2/personas.json`
  - `.audit/phase2/brand.json` (pour la voix de marque)
  - Liste de tous les wordings déjà collectés (cross-vues) — `.audit/wording-corpus.json` si existant
- **Output :** Section `wording` dans `.audit/screen-audits/screen-{n}.json` + mise à jour de `.audit/wording-corpus.json`

---

## Règle de description préalable

Avant toute évaluation, l'agent extrait et liste tous les textes fonctionnels visibles sur l'écran :

```
TEXTES EXTRAITS DE [URL] :
Labels de navigation : [liste]
Titres et sous-titres : [liste]
Labels de boutons/CTAs : [liste]
Labels de formulaires : [liste]
Placeholders : [liste]
Messages d'état visibles (erreur, succès, vide, chargement) : [liste ou "aucun visible"]
Tooltips visibles : [liste ou "aucun visible"]
Liens textuels : [liste des plus significatifs]
```

Cette extraction est **obligatoire** avant toute évaluation. Elle constitue le corpus de cet écran.

---

## Grille d'évaluation Wording

### 1. Cohérence terminologique (cross-vues)
Comparer les termes extraits avec `.audit/wording-corpus.json` (corpus des écrans déjà audités).
Signaler toute divergence pour un même concept :
- Même entité nommée différemment selon les écrans
- Même action libellée différemment selon les contextes
- Même état (erreur, succès) formulé différemment

**Format de signalement :**
```
INCOHÉRENCE : Le concept [X] est nommé "[terme A]" sur cet écran et "[terme B]" sur [écran Y].
```

### 2. Adéquation au persona

Pour chaque persona identifié dans `personas.json` (attribut `tech_literacy`) :

**Si tech_literacy = "débutant" :**
- Tous les termes techniques non expliqués sont des violations
- Les codes d'erreur bruts (404, 500, 403) sont des violations critiques
- Le jargon métier non défini est une violation haute

**Si tech_literacy = "intermédiaire" :**
- Les acronymes non développés au premier usage sont des violations
- Les messages d'erreur sans solution proposée sont des violations hautes

**Si tech_literacy = "expert" :**
- Le jargon métier et technique du domaine est acceptable
- Les termes excessivement simplifiés peuvent être signalés comme inutilement verbeux

**Règle de croisement :** Si plusieurs personas coexistent avec des niveaux différents, l'agent évalue pour le persona *le moins technique* présent — l'interface doit être accessible au niveau le plus bas tout en restant utile au niveau le plus haut.

### 3. Qualité des labels d'action (CTAs et boutons)

Évaluer chaque label de bouton selon ces critères :

| Critère | Acceptable | Problématique |
|---|---|---|
| Commence par un verbe | "Enregistrer", "Créer", "Supprimer" | "OK", "Oui", "Suite" |
| Décrit l'action réelle | "Supprimer le compte" | "Supprimer" (ambigu) |
| Cohérent avec l'action | "Envoyer" pour un formulaire d'envoi | "Valider" pour un envoi (imprécis) |
| Absence de jargon | "Télécharger le rapport" | "Export PDF payload" |

**Actions destructives :** le label doit nommer explicitement ce qui sera détruit.
"Supprimer cet utilisateur" est correct. "Supprimer" seul sur un modal de confirmation est insuffisant.

### 4. Qualité des messages d'état

**Empty states :** Pour chaque état vide détecté (pattern `length === 0`, `empty`, `no data`) :
- Un empty state muet (aucun texte, ou "Aucun résultat" uniquement) est une violation haute
- Un empty state correct contient : (a) pourquoi c'est vide, (b) une action pour remédier

**Messages d'erreur :** Appliquer la règle de Nielsen en 3 points :
1. CE QUI s'est passé ("Votre session a expiré")
2. POURQUOI ("Vous êtes resté inactif plus de 30 minutes")
3. COMMENT corriger ("Reconnectez-vous pour continuer")
Un message d'erreur qui ne satisfait pas les 3 points est une violation — noter combien de points manquent.

**États de chargement :** Un spinner sans texte est acceptable. Un spinner avec un message de contexte ("Chargement des rapports...") est meilleur. Un skeleton screen est optimal.

### 5. Charge textuelle et registre

- **Charge textuelle :** Compter le nombre de mots qu'un utilisateur doit lire avant de pouvoir effectuer l'action principale de cet écran. Seuil d'alerte : >50 mots obligatoires avant action.
- **Registre :** Identifier le registre dominant (formel, informel, technique, neutre). Signaler les ruptures de registre sur le même écran.
- **Voix de l'application :** Comparer avec `brand.json` (ton déclaré). Signaler les écarts.

---

## Output dans screen-{n}.json

```json
"wording": {
  "score": 0,
  "corpus": {
    "ctas": ["liste des labels de boutons extraits"],
    "navigation_labels": ["liste"],
    "form_labels": ["liste"],
    "placeholders": ["liste"],
    "error_messages": ["liste des messages d'erreur visibles"],
    "empty_states": ["liste des empty states visibles"],
    "headings": ["liste H1/H2/H3"]
  },
  "observations": [
    {
      "id": "word-001",
      "type": "terminology_inconsistency|cta_quality|error_message|empty_state|register_break|jargon|charge_textuelle",
      "severity": "critical|high|medium|low",
      "element": "bouton 'Valider' ligne 3 du formulaire",
      "observation": "Description factuelle précise du problème",
      "persona_impact": "Quel persona est impacté et comment",
      "recommendation": "Ce qui devrait être écrit à la place — sans réécrire le texte complet, indiquer le principe"
    }
  ],
  "register": "formel|informel|technique|neutre|mixte",
  "register_coherent": true,
  "jargon_violations": [],
  "missing_states": ["empty_state_users_list", "error_state_network"],
  "score_justification": "Justification en 2-3 lignes du score attribué"
}
```

---

## Mise à jour du wording-corpus.json

Après chaque écran audité, l'agent met à jour `.audit/wording-corpus.json` :

```json
{
  "last_updated": "ISO timestamp",
  "terms": {
    "Utilisateur": {
      "occurrences": [
        {"screen": "/users", "context": "titre de section"},
        {"screen": "/admin", "context": "label de tableau"}
      ],
      "variants_detected": ["Membre", "Compte"],
      "recommended_canonical": null
    }
  },
  "ctas_inventory": {
    "Enregistrer": ["/settings", "/profile"],
    "Valider": ["/checkout", "/forms/contact"],
    "Sauvegarder": ["/editor"]
  }
}
```

Ce fichier est la mémoire cross-vues du wording. Il permet à chaque instance de l'agent de détecter des incohérences sans avoir à relire tous les écrans précédents.

---

## Ancres de score — Wording

**Score 90-100 — Microcopy professionnel**
Terminologie 100% cohérente cross-vues. Chaque CTA commence par un verbe d'action précis. Tous les états (vide, erreur, chargement) ont un wording qui respecte la règle des 3 points. Registre uniforme et adapté au persona. Zéro jargon développeur exposé. La "voix" de l'application est reconnaissable et constante.

**Score 70-89 — Compétent avec lacunes**
La terminologie est majoritairement cohérente (1-2 écarts isolés). Les CTAs sont corrects mais certains manquent de précision contextuelle. Les messages d'erreur existent mais ne respectent pas toujours les 3 points. Registre globalement cohérent avec 1-2 ruptures.

**Score 50-69 — Problèmes significatifs**
Des incohérences terminologiques notables (même concept, noms différents sur 3+ écrans). Plusieurs CTAs génériques ("OK", "Continuer", "Valider" sans contexte). Des empty states muets ou réduits à "Aucune donnée". Messages d'erreur techniques exposés à des personas non-techniques.

**Score 30-49 — Problèmes majeurs**
Terminologie chaotique. CTAs qui n'indiquent pas l'action réelle. Codes d'erreur bruts exposés. Plusieurs états de l'interface sans aucun wording. Registre incohérent avec mélange formel/informel sur le même écran.

**Score 0-29 — Wording absent ou contre-productif**
L'interface n'a pas de wording pensé — les textes sont des reliquats de développement ("button1", "TODO", "test message"), des codes techniques bruts, ou une absence quasi-totale de guidance textuelle. Le wording existant crée activement de la confusion.

**Règle de calibration :** Si tu hésites entre deux tranches, choisis la plus basse et justifie pourquoi l'interface ne mérite pas la tranche supérieure.
```

---

## ÉTAPE 5 — Créer agents/19-ia-auditor.md

**Fichier :** `agents/19-ia-auditor.md`

```markdown
# Agent 19 — IA Auditor (Information Architecture)

## Identité
- **Discipline :** Architecture d'information et navigation
- **Phase :** Phase 3 — Audit transversal (une seule instance, pas par écran)
- **Spawné par :** 12-screen-dispatcher, une fois, après que tous les audits par écran sont lancés
- **Inputs :**
  - `.audit/page-map.json` (toutes les routes)
  - Code source de navigation (fichiers de routing, composants nav détectés dans `project-map.json`)
  - `.audit/phase2/personas.json` (tâches clés, mental models)
  - `.audit/interview.json` (tâches déclarées comme prioritaires)
  - `.audit/capabilities.json` (toutes les fonctionnalités disponibles)
- **Output :** `.audit/screen-audits/ia-audit.json` conforme à `schemas/ia-audit.schema.json`

---

## Règle de description préalable

Avant toute évaluation, l'agent reconstruit l'arbre de navigation complet depuis les fichiers sources :

```
ARBORESCENCE RECONSTITUÉE :

/ (Accueil)
├── /dashboard (Dashboard)
│   ├── /dashboard/reports (Rapports)
│   └── /dashboard/alerts (Alertes)
├── /users (Utilisateurs)
│   ├── /users/:id (Fiche utilisateur) [paramétré]
│   └── /users/new (Créer un utilisateur)
└── /settings (Paramètres)
    ├── /settings/profile
    └── /settings/security

Pages orphelines détectées (accessibles mais non dans l'arbre) :
- /export-temp
- /debug-panel

Profondeur maximale : 2
Nombre d'entrées au niveau 0 : 3
```

Cette reconstruction est **obligatoire** avant toute évaluation.

---

## Grille d'évaluation Architecture d'information

### 1. Métriques structurelles

Calculer et évaluer :

**Profondeur (depth)**
- ≤2 niveaux : optimal pour des outils de travail
- 3 niveaux : acceptable avec une navigation breadcrumb
- 4+ niveaux : problématique — l'utilisateur perd son orientation

**Largeur au niveau racine (breadth)**
- ≤5 entrées : optimal (loi de Hick — décision rapide)
- 6-7 entrées : acceptable
- 8+ entrées : dépasse le seuil de Hick — grouper par catégorie

**Pages orphelines**
Toute page présente dans `page-map.json` mais absente de l'arborescence de navigation est signalée. Une page orpheline est soit oubliée, soit intentionnelle (accès par lien direct uniquement) — les deux méritent d'être documentés.

**Symétrie des niveaux**
Si un niveau de l'arborescence contient 1 item d'un côté et 12 de l'autre, la structure est déséquilibrée. Calculer l'écart-type du nombre d'items par branche au même niveau.

### 2. Logique de groupement

La question centrale : **les items sont-ils groupés selon la logique du développeur ou la logique de l'utilisateur ?**

Deux types de logique de groupement à identifier :
- **Logique fonctionnelle** (par département, par module, par technologie) — souvent héritée de l'organisation du code
- **Logique de tâche** (par action utilisateur fréquente, par flux de travail) — centrée sur l'utilisateur

Pour chaque groupe de navigation identifié, poser la question : "Un utilisateur qui cherche à accomplir la tâche X trouverait-il naturellement ce groupe ?"

Comparer avec les `key_tasks` de chaque persona dans `personas.json`.

### 3. Alignement tâches/accès — mesure de distance

Pour chaque `key_task` déclarée dans `personas.json`, tracer le chemin depuis la racine :

```
Persona : [nom] — Tâche : "[tâche clé]"
Chemin trouvé : / → /[niveau1] → /[niveau2]
Distance : 2 clics
Acceptable : oui (seuil : ≤3 clics pour les tâches fréquentes)

---

Persona : [nom] — Tâche : "[tâche critique]"
Chemin trouvé : / → /admin → /admin/config → /admin/config/users → /admin/config/users/roles
Distance : 4 clics
Acceptable : NON — tâche fréquente à 4 clics est une violation haute
```

Seuils :
- Tâche fréquente (quotidienne) : ≤2 clics acceptable, 3 tolérable, 4+ violation
- Tâche importante (hebdomadaire) : ≤3 clics acceptable, 4 tolérable, 5+ violation
- Tâche rare (mensuelle) : profondeur plus grande acceptable

### 4. Qualité du labeling des nœuds de navigation

Pour chaque label de navigation :

**Labels problématiques à signaler :**
- Jargon technique ou développeur ("back-office", "CMS", "CRUD", "API keys" exposé à des non-techniques)
- Labels ambigus (deux sections différentes portant des noms similaires)
- Labels qui décrivent la structure interne plutôt que la tâche ("Module comptabilité" vs "Facturation")
- Labels trop génériques ("Divers", "Autres", "Général")
- Labels qui ne correspondent pas au contenu réel trouvé dans la section

**"Scent of information" :** le label doit permettre à l'utilisateur de *prédire* ce qu'il va trouver avant de cliquer. Évaluer chaque label : si quelqu'un qui n'a jamais vu ce logiciel lit ce label, sait-il ce qu'il va trouver ?

### 5. Navigation de retour et orientation

- Existe-t-il un breadcrumb sur les niveaux >1 ?
- L'élément actif de la navigation est-il toujours mis en évidence (état actif visible) ?
- Depuis n'importe quelle page, l'utilisateur peut-il revenir au niveau supérieur ?
- Y a-t-il des dead-ends (pages sans sortie sauf le bouton "retour" du navigateur) ?

---

## Ancres de score — Architecture d'information

**Sous-score : Depth (0-100)**
100 : Toutes les tâches fréquentes accessibles en ≤2 clics. Structure plate et logique.
70 : Majorité des tâches à ≤2 clics, quelques exceptions justifiées.
50 : Plusieurs tâches fréquentes à 3-4 clics. Navigation profonde non compensée par breadcrumb.
30 : Structure profonde, tâches fréquentes enfouies. Breadcrumb absent.
0 : Navigation à 5+ niveaux. Aucune tâche fréquente directement accessible.

**Sous-score : Breadth (0-100)**
100 : Niveau racine ≤5 entrées. Groupements naturels et non-chevauchants.
70 : 6-7 entrées, groupements cohérents.
50 : 8-10 entrées. Charge de décision élevée mais navigation possible.
30 : >10 entrées sans groupement secondaire. Loi de Hick violée.
0 : Navigation plate avec 15+ entrées non groupées.

**Sous-score : Grouping logic (0-100)**
100 : Tous les groupements reflètent les tâches et mental models des personas. Zéro logique développeur visible.
70 : Majorité centrée utilisateur, quelques groupements hérités de la structure technique.
50 : Mix 50/50. L'utilisateur doit apprendre la logique interne pour naviguer.
30 : Structure principalement technique. L'utilisateur doit mapper sa tâche sur la structure du code.
0 : Structure 1:1 avec l'architecture technique. Inutilisable sans formation.

**Sous-score : Labeling (0-100)**
100 : Tous les labels décrivent la tâche. Zéro jargon. "Scent of information" parfait.
70 : Majorité de labels clairs, quelques termes à clarifier.
50 : Plusieurs labels ambigus ou génériques. Quelques termes techniques.
30 : Labels majoritairement techniques ou ambigus. Difficile de prédire le contenu.
0 : Labels issus du code (noms de modules, identifiants techniques). Incompréhensibles sans formation.

**Sous-score : Task alignment (0-100)**
100 : 100% des tâches clés des personas accessibles en ≤2 clics.
70 : >80% des tâches à ≤2 clics.
50 : 50-80% des tâches à ≤3 clics. Quelques tâches importantes enfouies.
30 : <50% des tâches clés accessibles en ≤3 clics.
0 : Les tâches les plus fréquentes sont les plus difficiles à atteindre.

**Score global :** moyenne pondérée — Task alignment × 30% + Grouping logic × 25% + Labeling × 20% + Depth × 15% + Breadth × 10%.

**Règle de calibration :** Si tu hésites entre deux tranches, choisis la plus basse et justifie pourquoi l'interface ne mérite pas la tranche supérieure.
```

---

## ÉTAPE 6 — Créer agents/20-contextual-gaps-auditor.md

**Fichier :** `agents/20-contextual-gaps-auditor.md`

```markdown
# Agent 20 — Contextual Gaps Auditor

## Identité
- **Discipline :** Affordances contextuelles manquantes
- **Phase :** Phase 4 — Synthèse (en parallèle de 13-consistency-checker et 17-contradiction-detector)
- **Spawné par :** 00-orchestrator au démarrage de la Phase 4
- **Inputs :**
  - `.audit/capabilities.json` (toutes les fonctionnalités implémentées)
  - `.audit/phase2/personas.json` (tâches clés, scénarios, contextes d'usage)
  - `.audit/page-map.json` (toutes les vues)
  - Tous les `.audit/screen-audits/screen-{n}.json` (observations des 5 disciplines)
  - `.audit/interview.json` (tâches prioritaires déclarées)
- **Output :** `.audit/phase4/contextual-gaps.json` conforme à `schemas/contextual-gaps.schema.json`

---

## Méthode de travail

Cet agent ne regarde pas un écran en isolation. Il joue des **scénarios complets** et détecte les moments où le persona aurait besoin de X et ne peut pas y accéder depuis là où il se trouve.

### Étape 1 — Inventaire des capacités disponibles par vue

Construire une matrice :
```
capability_id | capability_name | views_where_exposed
cap-001       | Exporter en PDF | /reports, /report-detail
cap-002       | Filtrer par date | /reports
cap-003       | Contacter support | /account/help
cap-004       | Dupliquer un élément | /templates
```

Cette matrice révèle immédiatement les asymétries : une capacité exposée sur 1 seule vue alors que la logique d'usage suggère qu'elle devrait être accessible depuis N vues.

### Étape 2 — Simulation de scénarios persona

Pour chaque persona dans `personas.json`, pour chaque `key_task`, simuler le scénario :

```
Persona : [nom] — Tâche : "[tâche clé]"
Chemin naturel :
1. L'utilisateur arrive sur [vue de départ naturelle pour cette tâche]
2. Il cherche à [action intermédiaire]
3. Il aurait naturellement besoin de [capacité X]
4. [Capacité X] est-elle accessible depuis [cette vue] ? → OUI / NON
   → Si NON : gap identifié
```

### Étape 3 — Patterns de gaps à détecter systématiquement

L'agent cherche ces patterns en priorité :

**Pattern A — Le filtre orphelin**
Une capacité de filtrage existe sur la vue liste mais pas sur le tableau de bord qui affiche les mêmes données. L'utilisateur qui voit une anomalie sur le dashboard ne peut pas filtrer sans changer de vue.

**Pattern B — L'export inaccessible**
La capacité d'export existe sur une vue dédiée mais pas sur la vue de détail. L'utilisateur qui consulte un enregistrement spécifique ne peut pas l'exporter directement.

**Pattern C — Le support muet lors des erreurs**
Un lien "Contacter le support" existe dans les paramètres de compte. Il est absent des écrans d'erreur, des pages de timeout, et des vues de résultats vides. L'utilisateur qui a un problème ne trouve pas d'aide là où il en a besoin.

**Pattern D — L'action de contexte manquante**
Sur une vue liste, l'utilisateur peut cliquer sur un élément pour voir son détail. Depuis le détail, il peut le modifier. Mais il ne peut pas directement l'archiver, le dupliquer, ou le partager — des actions qui existent pourtant dans le système (dans `capabilities.json`) et qui seraient naturelles dans ce contexte.

**Pattern E — La navigation tronquée**
Depuis un enregistrement enfant (ex: `/projects/123/tasks/456`), l'utilisateur ne peut pas accéder directement aux autres enregistrements du parent (`/projects/123`) sans repasser par la navigation principale.

**Pattern F — L'information de contexte absente**
L'utilisateur est sur une vue d'action (ex: formulaire de commande) et aurait besoin d'une information de contexte (ex: le stock disponible, l'historique du client) qui existe dans le système mais n'est pas accessible sans quitter la vue en cours.

**Pattern G — La recherche partielle**
La capacité de recherche globale existe mais elle ne couvre pas tous les types d'entités. L'utilisateur cherche X depuis la barre de recherche principale et ne trouve pas X parce que X n'est pas indexé — mais X est accessible via un autre chemin.

### Étape 4 — Évaluation de la sévérité

Pour chaque gap identifié :

**Critique :** Le gap force le persona à interrompre sa tâche principale, à quitter sa vue de travail, et à naviguer vers une autre section pour effectuer une action qu'il devrait pouvoir faire depuis là où il est. La friction est directement quantifiable en clics ou en interruptions de flux.

**Haute :** Le gap crée une inefficacité notable mais l'utilisateur peut contourner en ≤2 étapes supplémentaires. Il le fera probablement mais avec frustration.

**Moyenne :** Le gap représente une opportunité d'amélioration. L'utilisateur a un chemin alternatif raisonnable mais moins efficace.

**Faible :** Le gap est une convenance. L'accès contextuel serait agréable mais son absence n'impacte pas significativement l'efficacité.

---

## Ancres de sévérité — Contextual Gaps

**Critique**
Le persona interrompt sa tâche principale. Exemple : un technicien qui diagnostique un incident réseau sur `/alerts/123` ne peut pas accéder à l'historique de la machine concernée sans quitter l'alerte, naviguer vers `/assets`, chercher la machine, et revenir. 4+ clics d'interruption pour une information directement liée.

**Haute**
Le contournement existe mais coûte du temps. Exemple : l'export d'un rapport individuel n'est pas possible depuis la vue détail — l'utilisateur doit retourner à la liste, filtrer pour retrouver ce rapport, puis exporter. 3 étapes supplémentaires.

**Moyenne**
Confort manquant. Exemple : le raccourci "Dupliquer" n'est pas disponible depuis la vue détail, seulement depuis la liste. L'utilisateur retourne à la liste, ce qui prend 1 clic de plus.

**Faible**
Nice to have. Exemple : le lien vers la documentation d'aide contextuelle de cette fonctionnalité spécifique n'est pas dans cette vue — l'aide générale est accessible depuis le menu principal.

---

## Règle anti-spéculation absolue

**L'agent 20 ne peut suggérer que des capacités déjà présentes dans `capabilities.json`.**

Si une capacité n'existe pas dans `capabilities.json`, l'agent ne peut pas créer un gap qui la réclame.
Il peut signaler que "la tâche [X] du persona [Y] n'a pas de support fonctionnel correspondant dans l'application" — mais c'est du ressort de l'agent 14 (functional-gap-analyst), pas du 20.

La distinction est importante :
- Agent 14 : "Cette fonctionnalité n'existe pas dans le code et devrait être créée"
- Agent 20 : "Cette fonctionnalité existe dans le code mais n'est pas accessible depuis le bon contexte"

---

## Format de chaque gap dans contextual-gaps.json

```json
{
  "id": "cgap-001",
  "severity": "critical",
  "persona_id": "persona-001",
  "scenario": "Le technicien vient de recevoir une alerte réseau critique. Il est sur /alerts/123 et cherche à voir l'historique de la machine concernée pour diagnostiquer.",
  "current_view": "/alerts/123",
  "missing_affordance": "Accès à l'historique de la machine concernée par l'alerte",
  "existing_location": "/assets/{id}/history",
  "capability_id": "cap-012",
  "evidence": "capabilities.json:cap-012 — 'Historique des assets' — implémenté, exposé sur /assets/:id/history",
  "recommendation": "Ajouter un lien contextuel 'Voir l'historique de [nom machine]' dans le panneau de détail de l'alerte, pointant vers /assets/{asset_id}/history",
  "effort": "xs",
  "type": "missing_context_info"
}
```

**Règle de précision :** Le champ `scenario` doit décrire une situation réelle et spécifique — pas "l'utilisateur veut accéder à X" mais "l'utilisateur est en train de [tâche précise], il vient de [action précédente], et il a besoin de [information/action] pour continuer".
```

---

## ÉTAPE 7 — Mettre à jour agents/12-screen-dispatcher.md

**Action :** Ajouter le spawn de l'agent 18 dans la liste des agents lancés par écran.

**Bloc à ajouter** dans la section "Agents lancés par écran" :
```markdown
Pour chaque page dans page-map.json, spawner en parallèle :
- 07-graphisme-auditor (discipline 1)
- 08-ui-auditor (discipline 2)
- 09-ux-auditor (discipline 3)
- 10-webdesign-auditor (discipline 4)
- 11-ihm-auditor (discipline 5)
- 18-wording-auditor (discipline 6 — nouveau)  ← AJOUTER

En une seule instance (pas par écran), spawner :
- 19-ia-auditor (transversal — architecture d'information)  ← AJOUTER
```

**Et dans la structure screen-{n}.json**, ajouter la section wording dans `disciplines` :
```json
"disciplines": {
  "graphisme": { ... },
  "ui": { ... },
  "ux": { ... },
  "webdesign": { ... },
  "ihm": { ... },
  "wording": { "score": 0, "observations": [], "recommendations": [] }
}
```

**Et ajouter le score wording dans le calcul du `global_score` :**
Réviser la formule : `global_score = moyenne des 6 disciplines` (était 5).

---

## ÉTAPE 8 — Mettre à jour agents/00-orchestrator.md

**Action :** Ajouter dans la section "Phase 4" le spawn du nouvel agent 20 :

```markdown
## Phase 4 — Cohérence et synthèse

Spawner en parallèle :
- 13-consistency-checker
- 14-functional-gap-analyst
- 17-contradiction-detector
- 20-contextual-gaps-auditor  ← AJOUTER

Attendre tous les outputs avant de passer en Phase 5.
```

**Et dans l'affichage d'état du pipeline**, ajouter les nouveaux fichiers outputs à vérifier :
- `.audit/wording-corpus.json` (produit par 18, mis à jour après chaque écran)
- `.audit/screen-audits/ia-audit.json` (produit par 19)
- `.audit/phase4/contextual-gaps.json` (produit par 20)

---

## ÉTAPE 9 — Mettre à jour agents/15-report-generator.md

**Action 1 :** Ajouter le score wording dans le tableau des scores par discipline :

```markdown
| Discipline | Score moyen | Meilleur écran | Pire écran |
|---|---|---|---|
| Graphisme | XX/100 | ... | ... |
| UI | XX/100 | ... | ... |
| UX | XX/100 | ... | ... |
| Web Design | XX/100 | ... | ... |
| IHM | XX/100 | ... | ... |
| Wording | XX/100 | ... | ... |
| **Global** | **XX/100** | | |
```

**Action 2 :** Ajouter la section "Architecture d'information" dans le rapport :

```markdown
## Architecture d'information

Insérer après la section "Cohérence inter-écrans" :

### Navigation globale
[Reprendre l'arbre reconstruit par 19-ia-auditor avec les principaux problèmes]

### Distance tâches / accès
[Tableau des tâches clés des personas avec leur distance en clics]

### Recommandations IA
[Top 5 des recommandations de 19-ia-auditor priorisées]
```

**Action 3 :** Ajouter la section "Gaps contextuels" dans le rapport :

```markdown
## Gaps contextuels — Fonctionnalités mal positionnées

Ces fonctionnalités existent dans le système mais sont inaccessibles là où les utilisateurs en ont besoin.

[Liste des gaps critiques et hauts de contextual-gaps.json, avec le scénario]

Note : Ces corrections sont souvent à effort très faible (xs ou s) pour un impact élevé.
```

**Action 4 :** Ajouter un résumé wording dans la section "Cohérence inter-écrans" :

```markdown
### Wording et terminologie cross-vues
[Reprendre les principales incohérences terminologiques de wording-corpus.json]
[Tableau des termes en conflit et recommandation de terme canonique]
```

---

## ÉTAPE 10 — Mettre à jour agents/00b-quality-gate.md

**Action :** Ajouter les vérifications post-Phase 3 pour les nouveaux outputs :

```markdown
**Vérifications supplémentaires après Phase 3 (v3) :**

- `wording-corpus.json` existe et contient au moins autant d'entrées que d'écrans audités
- Chaque `screen-{n}.json` contient une section `disciplines.wording` non vide
- `ia-audit.json` existe et sa section `navigation_tree` n'est pas vide
- `ia-audit.json` contient une entrée dans `task_coverage` pour chaque `key_task` de chaque persona

**Vérifications supplémentaires après Phase 4 (v3) :**

- `contextual-gaps.json` existe
- Chaque gap dans `contextual-gaps.json` a un `capability_id` qui existe dans `capabilities.json`
  (violation de la règle anti-spéculation si non respecté)
- Au moins un gap de type `missing_shortcut` ou `missing_context_info` est présent
  (un rapport sans aucun gap contextuel est suspect — signaler en warning)
```

---

## ÉTAPE 11 — Mettre à jour .claude-plugin/plugin.json → v0.3.0

**Action :** Ajouter les 3 nouveaux agents :

```json
{
  "name": "deep-ux",
  "version": "0.3.0",
  "agents": [
    "00-orchestrator",
    "00b-quality-gate",
    "01-interview-conductor",
    "02-capability-mapper",
    "03-token-extractor-agent",
    "04-persona-builder",
    "05-brand-auditor",
    "06-benchmark-researcher",
    "07-graphisme-auditor",
    "08-ui-auditor",
    "09-ux-auditor",
    "10-webdesign-auditor",
    "11-ihm-auditor",
    "12-screen-dispatcher",
    "13-consistency-checker",
    "14-functional-gap-analyst",
    "15-report-generator",
    "16-coverage-auditor",
    "17-contradiction-detector",
    "18-wording-auditor",
    "19-ia-auditor",
    "20-contextual-gaps-auditor"
  ],
  "commands": ["run", "diff"],
  "skills": ["ux-audit"]
}
```

---

## 9. Progression v3

CC coche chaque item après création ou modification :

### Nouveaux fichiers de vocabulaire
- [ ] `docs/vocabulaire-wording.md`

### Nouveaux schémas
- [ ] `schemas/ia-audit.schema.json`
- [ ] `schemas/contextual-gaps.schema.json`

### Nouveaux agents
- [ ] `agents/18-wording-auditor.md`
- [ ] `agents/19-ia-auditor.md`
- [ ] `agents/20-contextual-gaps-auditor.md`

### Agents mis à jour
- [ ] `agents/12-screen-dispatcher.md` (spawn agent 18 + score wording dans global)
- [ ] `agents/00-orchestrator.md` (spawn agent 20 en Phase 4 + nouveaux fichiers d'état)
- [ ] `agents/15-report-generator.md` (sections wording, IA, gaps contextuels)
- [ ] `agents/00b-quality-gate.md` (vérifications v3)

### Plugin manifest
- [ ] `.claude-plugin/plugin.json` (v0.3.0, 22 agents)

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
- [ ] `.audit-template/.env.example` (mise à jour)
- [ ] `CONTRIBUTING.md` (création)
- [ ] `.claude-plugin/plugin.json` (mise à jour)
- [ ] `CLAUDE.md` (mise à jour)
- [ ] `scripts/00-bootstrap.sh` (mise à jour)

### Nouveaux scripts
- [ ] `scripts/00b-estimate-run.py`

### Nouveaux agents
- [ ] `agents/00b-quality-gate.md`
- [ ] `agents/16-coverage-auditor.md`
- [ ] `agents/17-contradiction-detector.md`

### Agents mis à jour
- [ ] `agents/01-interview-conductor.md` (questions 15-16 + champs JSON)
- [ ] `agents/07-graphisme-auditor.md` (ancres de score)
- [ ] `agents/08-ui-auditor.md` (ancres de score)
- [ ] `agents/09-ux-auditor.md` (ancres de score)
- [ ] `agents/10-webdesign-auditor.md` (ancres de score)
- [ ] `agents/11-ihm-auditor.md` (ancres de score)
- [ ] `agents/15-report-generator.md` (matrice impact/effort + top 10 + contradictions)

### Nouvelles commandes
- [ ] `commands/diff.md`

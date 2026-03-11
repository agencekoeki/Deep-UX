# Audit de code — scripts/02-discover.py, 03-build-page-map.py, 04-screenshot.py

Date : 2026-03-11
Méthode : lecture statique du code, confrontation avec SPEC.md

---

## 1. scripts/02-discover.py

### CE QUE LE SCRIPT FAIT RÉELLEMENT

Le script parcourt l'arborescence du projet avec `os.walk`, filtre les dossiers dans `IGNORE_DIRS`, classe chaque fichier par extension dans un dict (`html`, `css`, `scss`, `js`, `jsx`, `tsx`, `vue`, `php`), et compte les lignes de code par type.

Il détecte le stack en lisant `package.json` (dependencies + devDependencies) et `composer.json`. Il cherche des entry points et des config files par une liste hardcodée de chemins candidats.

Il produit `.audit/project-map.json`. Si le fichier existe déjà avec le même `project_root`, il skip.

### ANGLES MORTS SILENCIEUX

1. **`.py` absent du scan (ligne 22-31)** — Le SPEC.md exige explicitement : "Inventorie tous les fichiers par type : `.html`, `.css`, `.scss`, `.js`, `.jsx`, `.tsx`, `.vue`, `.php`, `.py`". Le dict `FILE_EXTENSIONS` ne contient PAS `.py`. Les fichiers Python sont silencieusement ignorés. Aucun warning.

2. **`.ts` absent du scan** — Les fichiers `.ts` (pas `.tsx`, juste `.ts`) ne sont pas dans `FILE_EXTENSIONS`. Un projet Angular ou un backend TypeScript aura ses fichiers `.ts` invisibles. Pas de warning.

3. **Reprise aveugle** — Lignes 225-228 : si `project-map.json` existe et que `project_root` correspond, le script skip. Mais si le projet a changé (nouveaux fichiers, nouvelles deps), le script ne le sait pas. Il faut supprimer manuellement le fichier pour rescanner. Anti-drift respectée (ne pas écraser), mais la SPEC dit aussi "reprise automatique" — ici c'est un skip total, pas une reprise intelligente.

4. **Angular non détecté via fichier** — La détection Angular (ligne 102) ne cherche que `@angular/core` dans les deps. Si `package.json` est absent ou corrompu, un projet Angular avec `angular.json` présent ne sera pas détecté. La présence de `angular.json` dans `find_config_files` n'est pas croisée avec `detect_stack`.

5. **Svelte, SvelteKit, Astro, Remix, Gatsby absents** — Aucune détection pour ces frameworks modernes. Le script retournera `unknown` silencieusement.

### CAS NON COUVERTS

| Cas | Comportement actuel | Conséquence |
|---|---|---|
| Monorepo (apps/, packages/) | Scanne tout à plat | Mélange les fichiers de plusieurs apps, stack détecté = celui du root package.json |
| pnpm workspaces | `package.json` racine ne contient pas les deps des packages enfants | UI library et router non détectés |
| Projet Svelte/SvelteKit | `"svelte"` dans deps mais non reconnu | `stack.type = "unknown"` |
| Projet Astro | `"astro"` dans deps mais non reconnu | `stack.type = "unknown"` |
| Projet avec Bun (pas de node_modules) | `bower_components` dans IGNORE_DIRS mais pas les dirs Bun | Pas de problème, mais IGNORE_DIRS incomplet |
| Symlinks circulaires | `os.walk` suit les symlinks par défaut | Boucle infinie potentielle (pas `followlinks=False` explicite, mais Python 3 par défaut ne suit pas — OK) |

### CE QUI EST FRAGILE

1. **Détection framework mutuellement exclusive** — Lignes 110-131 : la détection framework est une cascade if/elif. Un projet qui a `next` ET `laravel` dans ses deps (monorepo full-stack) sera classé `next` uniquement. Le `framework` ne peut avoir qu'une valeur.

2. **Détection UI library premier match** — Lignes 134-143 : si un projet utilise Tailwind ET Bootstrap (migration en cours), seul Tailwind sera détecté.

3. **`count_lines` sur fichiers binaires** — Ligne 40-46 : si un fichier `.css` est en fait un fichier minifié d'une seule ligne de 500k caractères, `count_lines` retourne 1 mais charge tout le fichier en mémoire ligne par ligne. Pas de crash mais LOC non significatif.

### RECOMMANDATIONS DE CORRECTIFS

| Priorité | Correctif |
|---|---|
| **P0** | Ajouter `.py` et `.ts` dans `FILE_EXTENSIONS` — le SPEC l'exige explicitement |
| **P1** | Ajouter détection Svelte (`"svelte"`, `"@sveltejs/kit"`), Astro (`"astro"`), Remix (`"@remix-run/react"`) |
| **P1** | Détecter les monorepos (`workspaces` dans package.json) et avertir dans l'output |
| **P2** | Permettre la détection de plusieurs frameworks/ui_libraries (passer à des listes) |
| **P2** | Ajouter un champ `scan_warnings` dans l'output pour les cas ambigus |
| **P3** | Ajouter un mode `--force` pour rescanner même si le fichier existe |

---

## 2. scripts/03-build-page-map.py

### CE QUE LE SCRIPT FAIT RÉELLEMENT

Le script lit `project-map.json`, dispatche vers 4 extracteurs selon `stack.type` :
- **react** : cherche les conventions Next.js (`pages/`, `app/`) en parcourant le filesystem, puis fallback sur regex `<Route path="...">` dans les fichiers source
- **vue** : cherche la convention Nuxt (`pages/`), puis fallback sur regex `path: '...'` dans les fichiers router
- **static** : liste les `.html` et convertit les chemins en routes
- **php** : liste les `.php` en excluant vendor/config/migration/seed/test

Il déduplique par `url_or_path`, devine le `page_type` et `requires_auth` par des heuristiques sur le nom du chemin.

### ANGLES MORTS SILENCIEUX

1. **Aucun crawl web (SPEC ligne 227)** — Le SPEC dit : "Optionnel si URL fournie dans .env : crawl léger (depth=2, pas de JS) pour trouver les liens internes". Le script ne lit JAMAIS le `.env`, ne fait aucun crawl HTTP. Ce n'est pas un "optionnel non implémenté" — c'est qu'il n'y a même pas de tentative, pas de log "crawl: skipped (no BASE_URL)", rien.

2. **Angular = 0 pages, silencieusement** — Si `stack.type == "angular"`, le script tombe dans le fallback `else` (ligne 251) qui appelle `extract_pages_static + extract_pages_php`. Un projet Angular pur (pas de fichiers `.html` dans le root, pas de `.php`) produira **0 pages sans aucun avertissement**. L'orchestrateur va continuer avec un page-map vide.

3. **`guess_requires_auth` est une loterie** — Ligne 44-48 : toute URL qui ne contient pas "login/register/landing/home/index/about/contact/pricing" dans son nom est considérée comme nécessitant auth. `/api/health` → `requires_auth: true`. `/dashboard-public` → `requires_auth: true` (contient "dashboard" mais pas dans la whitelist). C'est un booléen qui impacte directement le comportement du screenshot (login ou pas).

4. **Routes paramétrées deviennent des routes littérales invalides** — Ligne 71 : `[id]` est transformé en `:id` → route `/user/:id`. Mais `04-screenshot.py` va tenter de naviguer vers `http://localhost:3000/user/:id` littéralement. Pas de mécanisme pour substituer un vrai ID.

### CAS NON COUVERTS

| Cas | Comportement actuel | Conséquence |
|---|---|---|
| **SPA avec routing JS pur** (pas de `<Route>`, router custom) | Regex `<Route path="...">` ne matche pas | 0 pages trouvées, page-map vide, audit impossible |
| **React Router v6 `createBrowserRouter`** | Le pattern `createBrowserRouter([{path: "/..."}])` n'est pas couvert par la regex `<Route path="...">` | 0 pages pour les projets RRv6 modernes |
| **TanStack Router** | Aucune détection | 0 pages |
| **Sitemap Yoast multi-niveaux** | Aucun parsing de sitemap | Les projets WordPress avec des centaines de pages ne sont pas découverts |
| **Pages derrière des états dynamiques** | Non couvert — le script ne regarde que les fichiers statiques | Les modals, drawers, onglets dynamiques sont invisibles |
| **URLs de ressources vs URLs de pages** | Pas de distinction — un fichier `api.php`, `helpers.php`, `utils.php` est traité comme une page | PHP : chaque fichier `.php` devient une "page", même les includes non-routables |
| **Domaines externes** | Non applicable (pas de crawl) | — |
| **Layouts/templates Next.js** | `layout.tsx`, `loading.tsx`, `error.tsx` dans `app/` sont traités comme des pages | Faux positifs : un `layout.tsx` n'est pas une page navigable |
| **Route groups Next.js `(group)/`** | Le `(group)` n'est pas stripé du chemin | Route `/\(marketing\)/about` au lieu de `/about` |
| **Catch-all routes `[...slug]`** | Transformé en `:...slug` | Route non navigable |

### CE QUI EST FRAGILE

1. **Regex React Router (ligne 87)** — `<Route\s+[^>]*path=["']([^"']+)["']` ne matche que le format JSX avec `<Route path="/foo">`. Ne matche pas :
   - `<Route path={ROUTES.HOME}>` (variable)
   - `{ path: "/foo", element: <Foo/> }` (objet dans createBrowserRouter)
   - Routes définies dans un fichier de config séparé

2. **Regex Vue Router (ligne 143)** — `path:\s*['"]([^'"]+)['"]` est trop large. Matche n'importe quel objet avec une clé `path` dans tout le fichier, y compris des commentaires, des objets non liés au routing.

3. **Heuristique `guess_page_type` (lignes 24-41)** — `/user/new` → "form" (correct). `/news` → "form" (faux : contient "new"). `/browse-settings` → "list" (faux : contient "browse"). Les substrings sans frontières de mots causent des faux positifs.

4. **Skip si page-map existe (ligne 232-234)** — Si un page-map existe mais est incomplet (crash pendant la construction), le script skip tout. Pas de vérification de complétude.

### RECOMMANDATIONS DE CORRECTIFS

| Priorité | Correctif |
|---|---|
| **P0** | Ajouter un extracteur Angular (`app-routing.module.ts`, routes déclaratives) |
| **P0** | Ajouter le parsing de `createBrowserRouter` / `createRoutesFromElements` pour React Router v6 |
| **P0** | Filtrer `layout.tsx`, `loading.tsx`, `error.tsx`, `not-found.tsx`, `template.tsx` dans l'extracteur Next.js App Router |
| **P1** | Implémenter le crawl léger (HTTP GET + parse des `<a href>`) si `BASE_URL` est défini dans `.env` |
| **P1** | Marquer les routes paramétrées (`:id`, `[slug]`) avec un champ `"parameterized": true` pour que `04-screenshot.py` puisse les traiter spécifiquement (ou les skip avec un warning) |
| **P1** | Stripper les route groups Next.js `(group)` du chemin |
| **P2** | Utiliser des word boundaries dans `guess_page_type` : `\bnew\b` au lieu de `"new"` |
| **P2** | Pour PHP : distinguer les fichiers routables (avec `<?php` en première ligne + output HTML) des includes/helpers |
| **P2** | Ajouter un champ `"discovery_method": "filesystem|router_parse|crawl"` pour tracer comment chaque page a été trouvée |
| **P3** | Implémenter le parsing de `sitemap.xml` / `sitemap_index.xml` pour WordPress/CMS |

---

## 3. scripts/04-screenshot.py

### CE QUE LE SCRIPT FAIT RÉELLEMENT

Le script lit `.env` via `get_auth_config()`, lit `page-map.json`, lance Playwright Chromium headless, gère l'authentification (form login avec heuristique de sélecteurs, ou SSO via storage state), puis itère sur chaque page pour faire un screenshot pleine page.

Chaque screenshot réussi met à jour `page-map.json` incrémentalement. Les erreurs sont loguées dans `screenshot-errors.json`.

### ANGLES MORTS SILENCIEUX

1. **Routes paramétrées (héritage de 03)** — Ligne 86-87 : si `url_or_path` est `/user/:id`, le script navigue vers `http://localhost:3000/user/:id` littéralement → 404 garantie. L'erreur est loguée dans `screenshot-errors.json`, mais rien n'indique que c'est un problème de route paramétrée, pas un vrai 404.

2. **`storage_state` attend un fichier, pas un dict** — Ligne 144 : `context_options["storage_state"] = auth_state` où `auth_state` est le retour de `load_auth_state()` qui fait `read_json()` → retourne un dict Python. Mais `browser.new_context(storage_state=...)` attend soit un **chemin de fichier** (string) soit un dict avec la structure exacte Playwright (`{"cookies": [...], "origins": [...]}`). Si le dict vient de `06-export-session-helper.py` (format custom), il manquera des champs requis par Playwright. Si `load_auth_state()` retourne un dict, il devrait retourner le **chemin du fichier** à la place pour être sûr.

3. **Login form : aucun feedback si aucun champ trouvé** — Lignes 35-65 : si aucun sélecteur ne matche pour username, password ou submit, le script ne fait rien du tout — pas de `fill`, pas de `click`. Il passe directement au `wait_for_url` qui va timeout au bout de 15s, log "redirection non détectée", puis continue à capturer toutes les pages sans auth. Toutes les captures seront des pages de login ou des redirections vers le login. Aucun avertissement explicite "champ de login non trouvé".

4. **Viewport mobile non implémenté** — Le `.env.example` v2 définit `SCREENSHOT_MOBILE=true` et `SCREENSHOT_MOBILE_WIDTH=375`, mais le script `04-screenshot.py` ne lit PAS ces variables. Il n'y a aucun code pour faire une seconde passe mobile. Les variables existent dans le `.env`, mais le script les ignore silencieusement.

5. **`SCREENSHOT_DELAY_MS` non implémenté** — Variable définie dans `.env.example` mais ignorée par le script. Pas de délai configurable avant capture.

6. **`PLAYWRIGHT_TIMEOUT_MS` non implémenté** — Variable définie dans `.env.example`, mais le timeout est hardcodé à `30000` (ligne 92).

7. **`EXCLUDE_URLS` non implémenté** — Variable définie dans `.env.example`, le script capture toutes les pages sans filtrage.

### CAS NON COUVERTS

| Cas | Comportement actuel | Conséquence |
|---|---|---|
| **SPA qui charge tout en JS** | `wait_until="networkidle"` attend que le réseau se calme, mais si le JS est lent (>30s) | Timeout, screenshot de page blanche ou spinner |
| **Pages avec lazy-loaded content** | Un screenshot est pris dès `networkidle` | Le contenu below-the-fold chargé en lazy loading peut ne pas être dans le screenshot |
| **Login avec MFA/CAPTCHA** | Le script essaie de remplir email + password + cliquer submit | MFA bloque, CAPTCHA bloque, aucun mécanisme de contournement ni message explicite |
| **Login avec champs custom** (ex: numéro de client + code PIN) | Seuls `email`, `username`, `password` sont cherchés | Champs non trouvés → login silencieusement raté |
| **Pages qui redirigent (301/302)** | Le screenshot capture la page de destination | Pas de log indiquant que la page a redirigé — l'URL dans page-map pointe vers l'original |
| **Pages avec cookie consent banner** | Le banner est capturé en plein écran | Tous les screenshots ont un banner de consentement en overlay — pollue l'audit |
| **Pages derrière basic auth HTTP** | Non géré | 401, erreur dans screenshot-errors.json |
| **Certificats SSL auto-signés (dev local)** | Chromium headless rejette les certificats invalides par défaut | Erreur TLS, aucune page capturée |
| **Domaines externes** | Si `page-map.json` contient une URL absolue vers un autre domaine | Le script la capture — pas de filtre de domaine |

### CE QUI EST FRAGILE

1. **Sélecteurs de login hardcodés** — Lignes 35-65 : les sélecteurs sont en cascade et s'arrêtent au premier match. Si la page a un `input[type="text"]` pour un champ de recherche AVANT le champ email, le script remplit le champ de recherche avec l'email. Pas de vérification que le champ est dans un formulaire de login.

2. **`networkidle` comme signal de chargement** — Playwright définit `networkidle` comme "plus de 2 requêtes réseau pendant 500ms". Sur des SPAs avec websockets, polling ou analytics, `networkidle` peut ne jamais être atteint → timeout à 30s.

3. **Sauvegarde incrémentale = file corruption risk** — Ligne 171 : `write_json(PAGE_MAP_PATH, page_map)` est appelé après chaque screenshot réussi. Si le script crash pendant l'écriture (kill -9, disque plein), le JSON sera corrompu. `write_json` dans `file_utils.py` fait un `open("w")` directement — pas d'écriture atomique (écriture dans .tmp puis rename).

4. **Accumulation d'erreurs** — Ligne 122 : `errors = read_json(ERRORS_PATH) or []`. Si le script est relancé, les anciennes erreurs sont lues mais les nouvelles sont **ajoutées**. Si la même page échoue 10 fois, on a 10 entrées d'erreur pour la même page. Pas de déduplication.

### RECOMMANDATIONS DE CORRECTIFS

| Priorité | Correctif |
|---|---|
| **P0** | Skip les routes paramétrées (`:id`, `[slug]`) avec un warning explicite, ou demander une valeur de test dans `.env` |
| **P0** | Implémenter la lecture de `EXCLUDE_URLS`, `SCREENSHOT_DELAY_MS`, `PLAYWRIGHT_TIMEOUT_MS` — ces variables sont promises à l'utilisateur dans `.env.example` |
| **P0** | Ajouter un warning explicite quand aucun champ de login n'est trouvé (username, password, ou submit) au lieu de continuer silencieusement |
| **P1** | Implémenter la capture mobile (`SCREENSHOT_MOBILE=true`) en 2e passe avec viewport 375px |
| **P1** | Passer `ignore_https_errors=True` dans `browser.new_context()` pour gérer les dev locaux avec certificats auto-signés |
| **P1** | Fixer `load_auth_state()` : retourner le chemin du fichier (string) au lieu du dict, OU valider que le dict a la structure Playwright attendue |
| **P1** | Rendre `write_json` atomique (écrire dans un `.tmp` puis `os.rename`) dans `lib/file_utils.py` |
| **P2** | Ajouter un mécanisme de cookie consent dismissal (chercher les boutons "Accept", "OK", "Fermer" avant la capture) |
| **P2** | Dédupliquer les erreurs dans `screenshot-errors.json` par `page_id` |
| **P2** | Détecter les redirections et logger l'URL finale réelle dans le page-map |
| **P3** | Ajouter un mode `--page=page-001` pour recapturer une seule page |
| **P3** | Ajouter un filtre de domaine pour ne pas capturer les URLs externes |

---

## Synthèse transversale

### Problèmes systémiques (affectent les 3 scripts)

1. **Pas de validation contre les schemas JSON** — Aucun script ne valide son output contre le schema correspondant. La SPEC dit "Schema strict" (règle anti-drift n°3), mais la validation n'est faite nulle part.

2. **Skip trop agressif** — Les 3 scripts skip complètement si le fichier output existe, sans vérifier s'il est complet ou corrompu. La SPEC dit "reprendre pas recréer" — mais "reprendre" implique de vérifier l'état, pas de skip aveugle.

3. **Variables `.env` v2 non lues** — Les variables ajoutées dans `.env.example` v2 (`EXCLUDE_URLS`, `CRAWL_DEPTH`, `SCREENSHOT_MOBILE`, `SCREENSHOT_DELAY_MS`, `PLAYWRIGHT_TIMEOUT_MS`, `DRY_RUN`) ne sont lues par aucun script.

4. **`write_json` non atomique** — Tout crash pendant une écriture corrompt le fichier, cassant la reprise.

### Top 5 des correctifs à faire en premier

1. **P0 — Ajouter `.py` et `.ts` dans `FILE_EXTENSIONS`** de 02-discover.py (violation directe du SPEC)
2. **P0 — Implémenter les variables `.env` v2** dans 04-screenshot.py (promesse non tenue à l'utilisateur)
3. **P0 — Gérer les routes paramétrées** dans la chaîne 03→04 (crash garanti sur tout projet avec des pages dynamiques)
4. **P0 — Ajouter extracteur Angular** dans 03-build-page-map.py (0 pages silencieusement pour tous les projets Angular)
5. **P1 — Rendre `write_json` atomique** dans lib/file_utils.py (risque de corruption sur crash)

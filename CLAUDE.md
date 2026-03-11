# CLAUDE.md — deep-ux orchestration master

## Ce que tu es
Tu es l'orchestrateur du plugin **deep-ux** — un système d'audit UX exhaustif et autonome pour Claude Code.

## Comment tu fonctionnes

### Pré-requis silencieux
Bootstrap (`.audit/` structure) — exécuté automatiquement si `.audit/` n'existe pas. Ce n'est pas une phase numérotée.

### Pipeline séquentiel strict
```
Phase 0 — Interview        → .audit/interview.json
       ↓ [00b-quality-gate]
Phase 1 — Discovery        → project-map, page-map, tokens, screenshots, capabilities
                              + 8 scripts de mesure : a11y, dom, semantic, readability,
                                touch-targets, keyboard-nav, contrast-real, motion
       ↓ [00b-quality-gate]
       ↓ [16-coverage-auditor — rapport de couverture, non bloquant]
Phase 2 — Grounding        → personas, brand, benchmarks
       ↓ [00b-quality-gate]
Phase 3 — Audit écrans     → .audit/screen-audits/screen-{id}.json
                              (5 disciplines + Wording) × N écrans
                              + 1 instance 19-ia-auditor (transversal)
       ↓ [00b-quality-gate]
Phase 4 — Cohérence        → consistency.json, functional-gaps.json, contradictions.json, contextual-gaps.json
       ↓ [00b-quality-gate]
Phase 5 — Rapports         → report-human.md, report-cc-tasks.json, report-client.html
```

### Règles absolues
1. **Séquentiel entre phases** — ne lance JAMAIS la phase N+1 avant que la phase N soit terminée
2. **Parallèle dans une phase** — les agents DANS une même phase peuvent tourner en parallèle
3. **Reprise automatique** — si relancé, reprend à la dernière phase incomplète
4. **Sauvegarde incrémentale** — chaque fichier est écrit dès qu'il est prêt
5. **Anti-drift** — chaque agent charge les skills `anti-drift` + sa skill disciplinaire (les `docs/` restent comme référence longue forme)
6. **Grounding fonctionnel** — aucune recommandation fonctionnelle sans `capability_id`

### Slash commands
- `/deep-ux:run` — lance l'audit complet (voir `commands/run.md`)
- `/deep-ux:diff` — compare deux runs d'audit (voir `commands/diff.md`)

### Fichiers de référence
- `SPEC.md` — spécification exhaustive (source de vérité)
- `docs/anti-drift-rules.md` — règles anti-drift
- `docs/grille-evaluation.md` — grilles de notation
- `docs/vocabulaire-*.md` — vocabulaire par discipline
- `schemas/*.schema.json` — schémas de validation JSON

## Agents de contrôle qualité

### 00b-quality-gate
Spawné par l'orchestrateur après chaque phase. Bloquant si des violations sont détectées.
Son output `.audit/quality-gates/gate-phase-{n}.json` doit avoir `"proceed": true` avant que l'orchestrateur ne continue.

### 16-coverage-auditor
Spawné après la Phase 1 (Discovery), avant la Phase 2 (Grounding). Son output informe le concepteur des angles morts.
Non bloquant — l'audit continue même si la couverture est partielle.

### 17-contradiction-detector
Spawné en Phase 4, en parallèle de 13-consistency-checker, 14-functional-gap-analyst et 20-contextual-gaps-auditor.
Son output est intégré dans le rapport final.

### 18-wording-auditor (outputs transversaux)
Spawné en Phase 3 pour chaque écran. Produit en plus un output transversal `.audit/wording-corpus.json`
qui agrège la terminologie cross-vues. Ce fichier est consommé en Phase 4 par le consistency-checker.

### 19-ia-auditor (output transversal)
Spawné une seule fois en Phase 3 (après tous les écrans). Produit `.audit/screen-audits/ia-audit.json`
qui reconstruit l'arbre de navigation et mesure la distance tâche/accès. Consommé en Phase 4 et Phase 5.

### 20-contextual-gaps-auditor
Spawné en Phase 4, en parallèle des autres agents Phase 4.
Détecte les fonctionnalités existantes mais inaccessibles là où l'utilisateur en a besoin.
Son output `.audit/phase4/contextual-gaps.json` est intégré dans le rapport final.

## Mode diff
La commande `/deep-ux:diff` est disponible après un premier run complet.
L'orchestrateur archive automatiquement chaque run terminé dans `.audit/archives/{timestamp}/`.

## Dossier quality-gates
Créer `.audit/quality-gates/` dans le bootstrap.

## Architecture des skills

deep-ux utilise 10 skills qui structurent la connaissance du système.

### Skills transversales (actives pour tous les agents)
- `ux-audit` — définition des 6 disciplines, règle des 3 temps, règle d'ancrage
- `anti-drift` — 7 règles de contrainte non négociables
- `json-output` — conventions de format, nommage, écriture atomique

### Skills disciplinaires (actives pour leur agent dédié)
- `graphisme` → agent 07
- `ui` → agent 08
- `ux` → agent 09
- `webdesign` → agent 10
- `ihm` → agent 11
- `wording` → agent 18

### Skill de calibration
- `scoring` — étalons de score par discipline

### Relation skills / docs
Les skills sont des distillations opérationnelles courtes.
Les `docs/` sont les sources de référence longue forme.
Les skills pointent vers les docs pour les définitions complètes.
En cas de contradiction : la skill prévaut (plus récente et plus précise).

### En cas de doute
Relis `SPEC.md`. Ne devine jamais.

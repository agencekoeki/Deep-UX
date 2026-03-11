# CLAUDE.md — deep-ux orchestration master

## Ce que tu es
Tu es l'orchestrateur du plugin **deep-ux** — un système d'audit UX exhaustif et autonome pour Claude Code.

## Comment tu fonctionnes

### Pipeline séquentiel strict
```
Phase 0 — Bootstrap        → .audit/ structure
Phase 1 — Interview        → .audit/interview.json
Phase 2 — Discovery        → project-map, page-map, tokens, screenshots, capabilities, personas, brand, benchmarks
Phase 3 — Audit écrans     → .audit/screen-audits/screen-{id}.json (5 disciplines × N écrans)
Phase 4 — Cohérence        → consistency.json, functional-gaps.json
Phase 5 — Rapports         → report-human.md, report-cc-tasks.json, report-client.html
```

### Règles absolues
1. **Séquentiel entre phases** — ne lance JAMAIS la phase N+1 avant que la phase N soit terminée
2. **Parallèle dans une phase** — les agents DANS une même phase peuvent tourner en parallèle
3. **Reprise automatique** — si relancé, reprend à la dernière phase incomplète
4. **Sauvegarde incrémentale** — chaque fichier est écrit dès qu'il est prêt
5. **Anti-drift** — chaque agent lit `docs/anti-drift-rules.md` et son vocabulaire disciplinaire
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

### En cas de doute
Relis `SPEC.md`. Ne devine jamais.

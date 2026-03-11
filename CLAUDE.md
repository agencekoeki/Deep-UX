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

### Slash command
`/deep-ux:run` — lance l'audit complet (voir `commands/run.md`)

### Fichiers de référence
- `SPEC.md` — spécification exhaustive (source de vérité)
- `docs/anti-drift-rules.md` — règles anti-drift
- `docs/grille-evaluation.md` — grilles de notation
- `docs/vocabulaire-*.md` — vocabulaire par discipline
- `schemas/*.schema.json` — schémas de validation JSON

### En cas de doute
Relis `SPEC.md`. Ne devine jamais.

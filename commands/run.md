# /deep-ux:run — Lance un audit UX complet

Tu es l'orchestrateur du plugin **deep-ux**. Tu vas lancer un audit UX exhaustif et autonome du projet courant.

## Étapes à suivre dans l'ordre strict

### Phase 0 — Bootstrap
1. Vérifie si `.audit/` existe. Si non, exécute `scripts/00-bootstrap.sh`.
2. Exécute `scripts/01-check-deps.sh`. Si exit code = 1, affiche les dépendances manquantes et STOPPE.

### Phase 1 — Interview du concepteur
1. Lis `.audit/interview.json`. Si `"status": "complete"`, affiche le résumé et demande confirmation pour continuer.
2. Si absent ou `"status": "in_progress"`, lance l'agent `agents/01-interview-conductor.md` pour interviewer l'utilisateur.
3. Attend que l'interview soit terminée avant de passer à la suite.

### Phase 2 — Discovery & Grounding
1. Exécute `python3 scripts/02-discover.py` → `.audit/project-map.json`
2. Exécute `python3 scripts/03-build-page-map.py` → `.audit/page-map.json`
3. Exécute `python3 scripts/05-extract-tokens.py` → `.audit/design-tokens.json`
4. Si `.audit/.env` indique `AUTH_TYPE=sso` et `.audit/auth-state.json` n'existe pas, lance `python3 scripts/06-export-session-helper.py` et attend l'utilisateur.
5. Exécute `python3 scripts/04-screenshot.py` → `.audit/screenshots/`
6. Lance l'agent `agents/02-capability-mapper.md` → `.audit/capabilities.json`
7. Lance l'agent `agents/03-token-extractor-agent.md` (analyse qualitative de design-tokens.json)
8. Lance l'agent `agents/04-persona-builder.md` → `.audit/phase2/personas.json`
9. Lance l'agent `agents/05-brand-auditor.md` → `.audit/phase2/brand.json`
10. Lance l'agent `agents/06-benchmark-researcher.md` → `.audit/phase2/benchmarks.json`

### Phase 3 — Audit par écran
1. Lance l'agent `agents/12-screen-dispatcher.md` qui :
   - Lit `page-map.json`
   - Pour chaque écran, lance les 5 agents d'audit (07 à 11) en parallèle
   - Consolide dans `.audit/screen-audits/screen-{page-id}.json`
2. Les écrans PEUVENT être audités en parallèle.

### Phase 4 — Cohérence et gaps
1. Lance l'agent `agents/13-consistency-checker.md` → `.audit/phase4/consistency.json`
2. Lance l'agent `agents/14-functional-gap-analyst.md` → `.audit/phase4/functional-gaps.json`

### Phase 5 — Rapports
1. Lance l'agent `agents/15-report-generator.md` qui produit :
   - `.audit/reports/report-human.md`
   - `.audit/reports/report-cc-tasks.json`
   - `.audit/reports/report-client.html`
2. Affiche le résumé exécutif à l'utilisateur.

## Affichage de progression

À chaque transition de phase, affiche :
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
deep-ux — État du pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Phase 0 — Bootstrap           [COMPLETE]
✓ Phase 1 — Interview           [COMPLETE]
→ Phase 2 — Discovery/Grounding [EN COURS]
  Phase 3 — Audit écrans        [EN ATTENTE]
  Phase 4 — Cohérence           [EN ATTENTE]
  Phase 5 — Rapports            [EN ATTENTE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Règles de l'orchestrateur
- JAMAIS deux phases en parallèle — séquentiel strict entre phases.
- Agents en parallèle DANS une même phase = OK (ex: 5 auditors sur un écran).
- Si un fichier output existe déjà → skip l'étape correspondante.
- Si une erreur survient → log l'erreur, tente de continuer avec les données disponibles.
- Sauvegarde incrémentale : chaque fichier produit est écrit immédiatement.

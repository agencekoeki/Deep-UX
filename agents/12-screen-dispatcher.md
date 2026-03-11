# Agent 12 — Screen Dispatcher

## Rôle
Tu lis `page-map.json` et lances les 5 agents d'audit (07 à 11) pour chaque écran. Tu consolides les résultats dans des fichiers `screen-{page-id}.json`.

## Inputs
- `.audit/page-map.json` — liste des pages
- Tous les fichiers Phase 2 :
  - `.audit/design-tokens.json`
  - `.audit/capabilities.json`
  - `.audit/phase2/personas.json`
  - `.audit/phase2/brand.json`
  - `.audit/phase2/benchmarks.json`

## Output
- `.audit/screen-audits/screen-{page-id}.json` pour chaque page — conforme à `schemas/screen-audit.schema.json`

## Processus

### 1. Lire page-map.json
Obtenir la liste complète des pages avec leurs screenshots.

### 2. Pour chaque page avec un screenshot
Lancer les 5 agents en parallèle :
- **Agent 07** — Graphisme Auditor → section `graphisme`
- **Agent 08** — UI Auditor → section `ui`
- **Agent 09** — UX Auditor → section `ux`
- **Agent 10** — Web Design Auditor → section `webdesign`
- **Agent 11** — IHM Auditor → section `ihm`

### 3. Consolider les résultats
Assembler les 5 sections dans un `screen-{page-id}.json` avec :
- `page_id`, `page_url`, `screenshot_path`, `audited_at`
- `disciplines` : les 5 sections d'audit
- `global_score` : moyenne pondérée (Graphisme 15%, UI 20%, UX 30%, Web Design 15%, IHM 20%)
- `critical_issues` : toutes les recommandations `"priority": "critical"` de toutes les disciplines
- `quick_wins` : toutes les recommandations avec `"priority": "high"` ou `"medium"` ET `"effort": "xs"` ou `"s"`

### 4. Mettre à jour page-map.json
Pour chaque page auditée, mettre `"audited": true`.

## Format des recommandations
Chaque recommandation dans chaque discipline DOIT suivre ce format strict :
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

## Anti-drift
- Skip les pages sans screenshot (log un warning)
- Skip les pages déjà auditées (si `screen-{page-id}.json` existe et est complet)
- Sauvegarde chaque `screen-{page-id}.json` dès qu'il est complet (incrémental)
- Les écrans PEUVENT être audités en parallèle entre eux

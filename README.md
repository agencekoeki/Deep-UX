# deep-ux

**Exhaustive UX/UI audit pipeline for Claude Code. Multi-agent, automated, grounded in your actual code.**

> Not a linter. Not a checklist. A full investigation of your interface — screen by screen, element by element — with personas, cross-screen consistency, and functional recommendations that never invent what doesn't exist in your codebase.

---

*🇫🇷 Version française disponible plus bas.*

---

## What deep-ux does

Point deep-ux at any web project. It runs on its own. At the end, you get:

- **Automatic screenshots** of every page, including behind authentication
- **Personas built** from your code AND an interview with the product designer
- **Screen-by-screen audit**: Nielsen heuristics, WCAG, visual consistency, relevance for the target user
- **Cross-screen consistency report**: terminology mismatches, contradictory interaction patterns, broken navigation flows
- **Grounded functional recommendations**: deep-ux never recommends a feature that doesn't exist in your code
- **Work tickets** ready to use in a Claude Code implementation session

---

## What deep-ux does NOT do

- It doesn't invent features. Every functional recommendation is tied to a real capability detected in your code, or explicitly tagged `[SPECULATION - TO VALIDATE]`
- It doesn't commit sensitive data. Auth credentials stay in `.audit/.env`, never in git
- It doesn't re-run completed phases. The pipeline resumes from where it stopped

---

## How it compares to existing UX skills

| | Existing UX skills | deep-ux |
|---|---|---|
| Analysis | File by file, on demand | Full automated pipeline |
| Screenshots | Manual | Playwright automatic, all pages |
| Auth | Not supported | Form login + SSO session export |
| Personas | No | Built from code + designer interview |
| Cross-screen consistency | No | Dedicated Phase 4 agent |
| Functional recommendations | Invented | Anchored to capabilities.json |
| Run time | A few minutes | Can run for hours unattended |

---

## Installation

```bash
# Inside your project folder
git clone https://github.com/koeki-agency/deep-ux .claude/plugins/deep-ux

# Then in Claude Code
/deep-ux:run
```

That's it. Claude Code takes over.

---

## What happens when you run `/deep-ux:run`

```
PHASE 0 — Interview (interactive, ~10 minutes)
  Claude asks you 12-15 questions about your users, known friction points,
  and your auth setup. Your answers shape everything that follows.

PHASE 1 — Discovery (automatic)
  Full file inventory, functional capability mapping from the code,
  design token extraction (colors, typography, spacing),
  Playwright screenshots of all pages.

PHASE 2 — Grounding (automatic)
  Persona construction from interview + sector analysis.
  Brand identity audit. Competitive benchmark.

PHASE 3 — Screen-by-screen audit (automatic, parallel)
  Each screen is analyzed independently by a dedicated agent.
  Input: screenshot + source code + personas + capabilities.

PHASE 4 — Cross-screen consistency (automatic)
  One agent re-reads all screen audits and looks for contradictions,
  terminology inconsistencies, pattern breaks.

PHASE 5 — Reports (automatic)
  Three formats: human-readable report, CC work tickets, client HTML report.
```

---

## Authentication

In Phase 0, Claude asks whether your project requires authentication.

**Form login** → Playwright connects automatically, saves the session, audits all protected pages.

**SSO / OAuth** → You export your storage state from your browser once. Playwright uses it for all captures.

**No auth** → Playwright runs without credentials. Protected pages are documented as "not automatically audited".

---

## Outputs

Everything lands in `.audit/` (auto-gitignored):

```
.audit/
├── reports/
│   ├── report-human.md          ← Direct reading, with priorities
│   ├── report-cc-tasks.json     ← Tickets ready for CC implementation
│   └── report-client.html       ← Presentable client version
├── screen-audits/               ← JSON per screen
├── phase4/
│   ├── consistency.json         ← Cross-screen consistency
│   └── functional-gaps.json     ← Functional gaps
└── screenshots/                 ← Full-page captures
```

---

## Requirements

- Claude Code with Bash access
- Python 3.8+
- Playwright (`pip install playwright && playwright install chromium`)
- Target project accessible locally or via URL

---

## Stack-agnostic by design

deep-ux works on any stack: static HTML, React, Vue, Angular, PHP, SaaS cockpit, business app. It analyzes what it finds. It makes no assumptions about your architecture.

---

## Contributing

This project is open. Issues, PRs and real-world feedback are welcome.

If you use it on a project, **a note on what worked and what broke** is more useful than a star.

---

## Authors

Built by **[Kōeki Agency](https://koeki.fr)** — SEO & AI consultancy, Tarascon, France.  
By [Sébastien Grillot](https://sebastiengrillot.com/a-propos/).

Initially developed to audit the IT cockpit of [Poweriti](https://poweriti.com).

---

*deep-ux is a Claude Code plugin. "Plugin" = a folder of text files that CC reads and executes. No binary, no compilation, no server.*

---

---

# deep-ux — Version française

**Pipeline d'audit UX/UI exhaustif pour Claude Code. Multi-agents, automatisé, ancré sur le code réel.**

> Pas un linter. Pas un checklist. Une investigation complète de votre interface — écran par écran, élément par élément — avec personas, cohérence inter-écrans, et recommandations fonctionnelles qui n'inventent jamais ce qui n'existe pas dans votre code.

---

## Ce que deep-ux fait concrètement

Vous pointez deep-ux sur n'importe quel projet web. Il tourne tout seul. À la fin, vous avez :

- **Des screenshots automatiques** de toutes vos pages, y compris derrière authentification
- **Des personas construits** à partir de votre code ET d'une interview du concepteur
- **Un audit écran par écran** : heuristiques Nielsen, WCAG, cohérence visuelle, pertinence pour la cible
- **Un rapport de cohérence inter-écrans** : incohérences de terminologie, patterns contradictoires, ruptures de navigation
- **Des recommandations fonctionnelles ancrées** : deep-ux ne recommande jamais une fonctionnalité qui n'existe pas dans votre code
- **Des tickets de travail** directement exploitables dans une session Claude Code

---

## Ce que deep-ux ne fait PAS

- Il n'invente pas de fonctionnalités. Chaque recommandation fonctionnelle est liée à une capacité réelle détectée dans votre code, ou est explicitement marquée `[SPÉCULATION - À VALIDER]`
- Il ne commit pas de données sensibles. Les credentials d'authentification restent dans `.audit/.env`, jamais dans git
- Il ne relance pas une phase déjà complétée. Le pipeline est repris là où il s'est arrêté

---

## Différence avec les autres skills UX

| | Skills UX existantes | deep-ux |
|---|---|---|
| Analyse | Fichier par fichier, à la demande | Pipeline complet automatique |
| Screenshots | Manuel | Playwright automatique, toutes pages |
| Auth | Non supporté | Login classique + export session SSO |
| Personas | Non | Construits à partir du code + interview |
| Cohérence inter-écrans | Non | Agent dédié Phase 4 |
| Recommandations fonctionnelles | Inventées | Ancrées sur capabilities.json |
| Durée | Quelques minutes | Peut tourner des heures sans supervision |

---

## Installation

```bash
# Dans le dossier de votre projet
git clone https://github.com/koeki-agency/deep-ux .claude/plugins/deep-ux

# Puis dans Claude Code
/deep-ux:run
```

C'est tout. Claude Code prend la main.

---

## Ce qui se passe quand vous lancez `/deep-ux:run`

```
PHASE 0 — Interview (interactive, ~10 minutes)
  Claude vous pose 12-15 questions sur vos utilisateurs, vos frictions connues,
  votre stack d'auth. Vos réponses conditionnent tout ce qui suit.

PHASE 1 — Discovery (automatique)
  Inventaire de tous les fichiers, cartographie des capacités fonctionnelles
  dans le code, extraction des design tokens (couleurs, typo, espacements),
  screenshots Playwright de toutes les pages.

PHASE 2 — Grounding (automatique)
  Construction des personas à partir de l'interview + analyse du secteur.
  Audit de l'identité de marque. Benchmark concurrentiel.

PHASE 3 — Audit par écran (automatique, parallèle)
  Chaque écran est analysé indépendamment par un agent dédié.
  Input : screenshot + code source + personas + capabilities.

PHASE 4 — Cohérence inter-écrans (automatique)
  Un agent relit tous les audits d'écrans et cherche les contradictions,
  incohérences de terminologie, ruptures de patterns.

PHASE 5 — Rapports (automatique)
  Trois formats : rapport humain lisible, tickets CC, rapport client HTML.
```

---

## Gestion de l'authentification

À la Phase 0, Claude vous demande si votre projet nécessite une authentification.

**Login classique (form)** → Playwright se connecte automatiquement, sauvegarde la session, audite toutes les pages protégées.

**SSO / OAuth** → Vous exportez votre storage state depuis votre navigateur une fois. Playwright l'utilise pour toutes les captures.

**Pas d'auth** → Playwright tourne sans credentials. Les pages protégées sont documentées comme "non auditées automatiquement".

---

## Outputs

Tout est dans `.audit/` (gitignored automatiquement) :

```
.audit/
├── reports/
│   ├── report-human.md          ← Lecture directe, avec priorités
│   ├── report-cc-tasks.json     ← Tickets exploitables dans CC
│   └── report-client.html       ← Version présentable au client
├── screen-audits/               ← JSON par écran
├── phase4/
│   ├── consistency.json         ← Cohérence inter-écrans
│   └── functional-gaps.json     ← Écarts fonctionnels
└── screenshots/                 ← Captures pleine page
```

---

## Prérequis

- Claude Code avec accès Bash
- Python 3.8+
- Playwright (`pip install playwright && playwright install chromium`)
- Le projet cible doit être accessible localement ou via URL

---

## Agnostique par design

deep-ux fonctionne sur n'importe quel stack : HTML statique, React, Vue, Angular, PHP, cockpit SaaS, app métier. Il analyse ce qu'il trouve. Il ne présuppose rien sur votre architecture.

---

## Contribuer

Ce projet est ouvert. Issues, PRs et retours d'expérience sont les bienvenus.

Si vous l'utilisez sur un projet, **un retour sur ce qui a bien fonctionné et ce qui a raté** est plus utile qu'une star.

---

## Auteurs

Construit par **[Kōeki Agency](https://koeki.fr)** — agence SEO & IA, Tarascon.  
Par [Sébastien Grillot](https://sebastiengrillot.com/a-propos/).

Initialement développé pour auditer le cockpit IT de [Poweriti](https://poweriti.com).

---

*deep-ux est un plugin Claude Code. "Plugin" = un dossier de fichiers texte que CC lit et exécute. Pas de binaire, pas de compilation, pas de serveur.*
